from typing import Any

from elasticsearch import AsyncElasticsearch

from app.core.config import Settings
from app.core.text import normalize_text
from app.repositories.base import RepositoryUnavailableError
from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions


class ElasticsearchContractorRepository:
    def __init__(self, settings: Settings) -> None:
        self._index = settings.elasticsearch_index
        self._max_candidates = settings.max_candidates
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
        query = {
            "bool": {
                "filter": [
                    {"term": {"city.normalized": normalize_text(city)}},
                    {"term": {"categories.normalized": normalize_text(category)}},
                ]
            }
        }
        if search_text:
            query["bool"]["should"] = [
                {"match": {"description": {"query": search_text, "boost": 1.0}}}
            ]
        try:
            response = await self._client.search(
                index=self._index,
                query=query,
                size=self._max_candidates,
            )
            contractors: list[Contractor] = []
            for hit in response["hits"]["hits"]:
                contractor = Contractor.model_validate(hit["_source"])
                contractors.append(
                    contractor.model_copy(
                        update={"search_relevance": float(hit.get("_score") or 0)}
                    )
                )
            return contractors
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

