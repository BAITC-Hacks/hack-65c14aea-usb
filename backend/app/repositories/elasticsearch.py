import asyncio
from typing import Any

from elasticsearch import AsyncElasticsearch

from app.core.config import Settings
from app.core.text import normalize_text
from app.repositories.base import RepositoryUnavailableError
from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions
from app.services.embeddings import EmbeddingService


class ElasticsearchContractorRepository:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self._index = settings.elasticsearch_index
        self._max_candidates = settings.max_candidates
        self._semantic_weight = settings.semantic_search_weight
        self._lexical_weight = settings.lexical_search_weight
        self._embeddings = embedding_service or EmbeddingService(settings)
        self._client = AsyncElasticsearch(
            settings.elasticsearch_url,
            request_timeout=settings.elasticsearch_request_timeout,
            max_retries=0,
            retry_on_timeout=False,
        )

    async def list_by_city_and_category(
        self,
        city: str,
        category: str,
        search_text: str | None = None,
    ) -> list[Contractor]:
        semantic_text = search_text or category
        query_vector = await asyncio.to_thread(
            self._embeddings.embed_query,
            semantic_text,
        )
        filtered_query: dict[str, Any] = {
            "bool": {
                "filter": [
                    {"term": {"city.normalized": normalize_text(city)}},
                    {"term": {"categories.normalized": normalize_text(category)}},
                ]
            }
        }
        if search_text:
            filtered_query["bool"]["should"] = [
                {"match": {"description": {"query": search_text, "boost": 1.0}}}
            ]
        query = {
            "script_score": {
                "query": filtered_query,
                "script": {
                    "source": (
                        "double semantic = "
                        "(cosineSimilarity(params.query_vector, "
                        "'profile_embedding') + 1.0) / 2.0; "
                        "double lexical = Math.min(_score / 8.0, 1.0); "
                        "return Math.max(0.000001, "
                        "params.semantic_weight * semantic + "
                        "params.lexical_weight * lexical);"
                    ),
                    "params": {
                        "query_vector": query_vector,
                        "semantic_weight": self._semantic_weight,
                        "lexical_weight": self._lexical_weight,
                    },
                },
            }
        }
        try:
            response = await self._client.search(
                index=self._index,
                query=query,
                size=self._max_candidates,
            )
            parsed: list[Contractor] = []
            for hit in response["hits"]["hits"]:
                source = dict(hit["_source"])
                source.pop("profile_embedding", None)
                contractor = Contractor.model_validate(source)
                parsed.append(
                    contractor.model_copy(
                        update={"search_relevance": float(hit.get("_score") or 0)}
                    )
                )
            evidence = await asyncio.to_thread(
                self._embeddings.best_evidence_batch,
                [contractor.description for contractor in parsed],
                query_vector,
            )
            return [
                contractor.model_copy(
                    update={
                        "semantic_relevance": relevance,
                        "semantic_evidence": sentence,
                    }
                )
                for contractor, (relevance, sentence) in zip(
                    parsed,
                    evidence,
                    strict=True,
                )
            ]
        except Exception as exc:
            raise RepositoryUnavailableError("Elasticsearch search failed") from exc

    async def catalog_options(self) -> CatalogOptions:
        aggregations: dict[str, Any] = {
            "cities": {"terms": {"field": "city", "size": 100}},
            "categories": {"terms": {"field": "categories", "size": 200}},
            "event_formats": {"terms": {"field": "event_formats", "size": 100}},
            "languages": {"terms": {"field": "languages", "size": 100}},
        }
        try:
            response = await self._client.search(
                index=self._index,
                size=0,
                aggs=aggregations,
            )
            values = response["aggregations"]
            return CatalogOptions(
                cities=_bucket_keys(values["cities"]),
                categories=_bucket_keys(values["categories"]),
                event_formats=_bucket_keys(values["event_formats"]),
                languages=_bucket_keys(values["languages"]),
            )
        except Exception as exc:
            raise RepositoryUnavailableError("Elasticsearch aggregation failed") from exc

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping()) and bool(
                await self._client.indices.exists(index=self._index)
            )
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.close()


def _bucket_keys(aggregation: dict[str, Any]) -> list[str]:
    return sorted(str(bucket["key"]) for bucket in aggregation["buckets"])
