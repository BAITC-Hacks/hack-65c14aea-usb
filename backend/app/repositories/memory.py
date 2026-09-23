from app.core.text import normalize_text
from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions


class MemoryContractorRepository:
    def __init__(self, contractors: list[Contractor]) -> None:
        self._contractors = list(contractors)

    async def list_by_city_and_category(
        self,
        city: str,
        category: str,
        search_text: str | None = None,
    ) -> list[Contractor]:
        city_key = normalize_text(city)
        category_key = normalize_text(category)
        return [
            contractor
            for contractor in self._contractors
            if normalize_text(contractor.city) == city_key
            and category_key in {normalize_text(item) for item in contractor.categories}
        ]

    async def catalog_options(self) -> CatalogOptions:
        return CatalogOptions(
            cities=sorted({item.city for item in self._contractors}),
            categories=sorted({value for item in self._contractors for value in item.categories}),
            event_formats=sorted(
                {value for item in self._contractors for value in item.event_formats}
            ),
            languages=sorted({value for item in self._contractors for value in item.languages}),
        )

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None

