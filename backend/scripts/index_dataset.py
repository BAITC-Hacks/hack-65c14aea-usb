#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path
from typing import Any

from elasticsearch import AsyncElasticsearch
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.contractor import Contractor
from app.services.embeddings import EmbeddingService, contractor_embedding_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index contractor JSONL into Elasticsearch")
    parser.add_argument(
        "dataset",
        nargs="?",
        type=Path,
        default=Path("data/hackathon-dataset-anonymized.jsonl"),
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete the configured index before importing",
    )
    return parser.parse_args()


def read_dataset(path: Path) -> list[Contractor]:
    contractors: list[Contractor] = []
    ids: set[str] = set()
    with path.open("r", encoding="utf-8") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                contractor = Contractor.model_validate_json(line)
            except ValidationError as exc:
                raise ValueError(f"Invalid profile at line {line_number}: {exc}") from exc
            if contractor.id in ids:
                raise ValueError(f"Duplicate contractor id at line {line_number}: {contractor.id}")
            contractors.append(contractor)
            ids.add(contractor.id)
    if not contractors:
        raise ValueError("Dataset is empty")
    return contractors


def index_definition(embedding_dimensions: int = 384) -> dict[str, Any]:
    normalized_field = {
        "type": "keyword",
        "fields": {"normalized": {"type": "keyword", "normalizer": "folded"}},
    }
    return {
        "settings": {
            "number_of_shards": 1,
            "analysis": {
                "normalizer": {
                    "folded": {
                        "type": "custom",
                        "filter": ["lowercase", "asciifolding"],
                    }
                }
            }
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "anon_name": {"type": "keyword"},
                "categories": normalized_field,
                "city": normalized_field,
                "price_from_kzt": {"type": "long"},
                "event_formats": normalized_field,
                "languages": normalized_field,
                "max_hours": {"type": "float"},
                "busy_dates": {"type": "date", "format": "strict_date"},
                "description": {"type": "text", "analyzer": "russian"},
                "synthetic": {"type": "boolean"},
                "city_imputed": {"type": "boolean"},
                "price_imputed": {"type": "boolean"},
                "profile_embedding": {
                    "type": "dense_vector",
                    "dims": embedding_dimensions,
                    "index": False,
                },
            },
        },
    }


async def index_contractors(
    client: AsyncElasticsearch,
    index_name: str,
    contractors: list[Contractor],
    recreate: bool,
    embedding_service: EmbeddingService,
) -> None:
    exists = await client.indices.exists(index=index_name)
    if exists and recreate:
        await client.indices.delete(index=index_name)
        exists = False
    if not exists:
        definition = index_definition(embedding_service.dimensions)
        await client.indices.create(
            index=index_name,
            settings=definition["settings"],
            mappings=definition["mappings"],
        )

    embeddings = embedding_service.embed_documents(
        [contractor_embedding_text(contractor) for contractor in contractors]
    )
    operations: list[dict[str, Any]] = []
    for contractor, embedding in zip(contractors, embeddings, strict=True):
        operations.append({"index": {"_index": index_name, "_id": contractor.id}})
        document = contractor.model_dump(mode="json")
        document["profile_embedding"] = embedding
        operations.append(document)
    response = await client.bulk(
        operations=operations,
        refresh="wait_for",
        request_timeout=30,
    )
    if response.get("errors"):
        failures = [
            item for item in response["items"] if item["index"].get("error")
        ]
        raise RuntimeError(f"Elasticsearch rejected {len(failures)} documents")


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    contractors = read_dataset(args.dataset)
    embedding_service = EmbeddingService(settings)
    client = AsyncElasticsearch(
        settings.elasticsearch_url,
        request_timeout=settings.elasticsearch_request_timeout,
    )
    try:
        await index_contractors(
            client,
            settings.elasticsearch_index,
            contractors,
            args.recreate,
            embedding_service,
        )
    finally:
        await client.close()
    print(f"Indexed {len(contractors)} profiles into {settings.elasticsearch_index}")


if __name__ == "__main__":
    asyncio.run(main())

