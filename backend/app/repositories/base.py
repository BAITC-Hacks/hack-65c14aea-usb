from typing import Protocol

from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions


class RepositoryUnavailableError(RuntimeError):
    """The configured contractor storage cannot serve the request."""


class ContractorRepository(Protocol):
    async def list_by_city_and_category(
        self,
        city: str,
        category: str,
        search_text: str | None = None,
    ) -> list[Contractor]:
        ...

    async def catalog_options(self) -> CatalogOptions:
        ...

    async def ping(self) -> bool:
        ...

    async def close(self) -> None:
        ...

