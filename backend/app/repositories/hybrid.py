import asyncio

from app.core.config import Settings
from app.repositories.elasticsearch import ElasticsearchContractorRepository
from app.repositories.postgres import PostgresContractorRepository
from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions


class HybridContractorRepository:
    """Elasticsearch ranks candidates; PostgreSQL owns catalog data."""

    def __init__(self, settings: Settings) -> None:
        self._search = ElasticsearchContractorRepository(settings)
        self._catalog = PostgresContractorRepository(settings)

    async def list_by_city_and_category(
        self,
        city: str,
        category: str,
        search_text: str | None = None,
    ) -> list[Contractor]:
        return await self._search.list_by_city_and_category(
            city,
            category,
            search_text,
        )

    async def catalog_options(self) -> CatalogOptions:
        return await self._catalog.catalog_options()

    async def ping(self) -> bool:
        search_ready, catalog_ready = await asyncio.gather(
            self._search.ping(),
            self._catalog.ping(),
        )
        return search_ready and catalog_ready

    async def close(self) -> None:
        await asyncio.gather(
            self._search.close(),
            self._catalog.close(),
            return_exceptions=True,
        )

