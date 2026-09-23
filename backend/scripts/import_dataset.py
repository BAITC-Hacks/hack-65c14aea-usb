#!/usr/bin/env python3
import argparse
import asyncio
import csv
from pathlib import Path

from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.database.models import Base, ContractorRow
from app.schemas.contractor import Contractor
from app.services.embeddings import EmbeddingService
from scripts.index_dataset import index_contractors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import contractor CSV into PostgreSQL and Elasticsearch"
    )
    parser.add_argument(
        "dataset",
        nargs="?",
        type=Path,
        default=Path("data/hackathon-dataset-anonymized.csv"),
    )
    return parser.parse_args()


def read_csv_dataset(path: Path) -> list[Contractor]:
    contractors: list[Contractor] = []
    ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = set(Contractor.model_fields) - {
            "search_relevance",
            "semantic_relevance",
            "semantic_evidence",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, start=2):
            contractor = Contractor.model_validate(
                {
                    "id": row["id"],
                    "anon_name": row["anon_name"],
                    "categories": _split(row["categories"]),
                    "city": row["city"],
                    "city_imputed": _parse_bool(row["city_imputed"]),
                    "synthetic": _parse_bool(row["synthetic"]),
                    "price_from_kzt": row["price_from_kzt"],
                    "price_imputed": _parse_bool(row["price_imputed"]),
                    "event_formats": _split(row["event_formats"]),
                    "languages": _split(row["languages"]),
                    "max_hours": row["max_hours"] or None,
                    "busy_dates": _split(row["busy_dates"]),
                    "description": row["description"],
                }
            )
            if contractor.id in ids:
                raise ValueError(
                    f"Duplicate contractor id at line {line_number}: {contractor.id}"
                )
            contractors.append(contractor)
            ids.add(contractor.id)
    if not contractors:
        raise ValueError("CSV dataset is empty")
    return contractors


async def sync_postgres(
    contractors: list[Contractor],
    database_url: str,
) -> None:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        rows = [_database_values(contractor) for contractor in contractors]
        statement = insert(ContractorRow).values(rows)
        update_columns = {
            key: getattr(statement.excluded, key)
            for key in rows[0]
            if key != "id"
        }
        update_columns["updated_at"] = func.now()
        async with sessions.begin() as session:
            await session.execute(
                statement.on_conflict_do_update(
                    index_elements=[ContractorRow.id],
                    set_=update_columns,
                )
            )
            await session.execute(
                delete(ContractorRow).where(
                    ~ContractorRow.id.in_([item.id for item in contractors])
                )
            )
    finally:
        await engine.dispose()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    contractors = read_csv_dataset(args.dataset)
    embedding_service = EmbeddingService(settings)
    await sync_postgres(contractors, settings.database_url)

    elasticsearch = AsyncElasticsearch(
        settings.elasticsearch_url,
        request_timeout=settings.elasticsearch_request_timeout,
    )
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await index_contractors(
            elasticsearch,
            settings.elasticsearch_index,
            contractors,
            recreate=True,
            embedding_service=embedding_service,
        )
        await redis.flushdb()
    finally:
        await elasticsearch.close()
        await redis.aclose()

    synthetic_count = sum(item.synthetic for item in contractors)
    print(
        f"Imported {len(contractors)} profiles "
        f"({synthetic_count} synthetic) into PostgreSQL and Elasticsearch"
    )


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def _parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _database_values(contractor: Contractor) -> dict[str, object]:
    return {
        "id": contractor.id,
        "anon_name": contractor.anon_name,
        "categories": contractor.categories,
        "city": contractor.city,
        "city_imputed": contractor.city_imputed,
        "synthetic": contractor.synthetic,
        "price_from_kzt": contractor.price_from_kzt,
        "price_imputed": contractor.price_imputed,
        "event_formats": contractor.event_formats,
        "languages": contractor.languages,
        "max_hours": contractor.max_hours,
        "busy_dates": contractor.busy_dates,
        "description": contractor.description,
    }


if __name__ == "__main__":
    asyncio.run(main())

