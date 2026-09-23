from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.text import normalize_text
from app.database.models import ContractorRow
from app.repositories.base import RepositoryUnavailableError
from app.schemas.contractor import Contractor
from app.schemas.recommendation import CatalogOptions


class PostgresContractorRepository:
    def __init__(self, settings: Settings) -> None:
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
        )
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def list_by_city_and_category(
        self,
        city: str,
        category: str,
        search_text: str | None = None,
    ) -> list[Contractor]:
        try:
            async with self._sessions() as session:
                result = await session.scalars(
                    select(ContractorRow).where(
                        func.lower(ContractorRow.city) == city.casefold()
                    )
                )
                category_key = normalize_text(category)
                return [
                    _to_contractor(row)
                    for row in result
                    if category_key
                    in {normalize_text(value) for value in row.categories}
                ]
        except Exception as exc:
            raise RepositoryUnavailableError("PostgreSQL query failed") from exc

    async def catalog_options(self) -> CatalogOptions:
        try:
            async with self._sessions() as session:
                rows = list(await session.scalars(select(ContractorRow)))
            return CatalogOptions(
                cities=sorted({row.city for row in rows}),
                categories=sorted(
                    {value for row in rows for value in row.categories}
                ),
                event_formats=sorted(
                    {value for row in rows for value in row.event_formats}
                ),
                languages=sorted(
                    {value for row in rows for value in row.languages}
                ),
            )
        except Exception as exc:
            raise RepositoryUnavailableError("PostgreSQL catalog query failed") from exc

    async def ping(self) -> bool:
        try:
            async with self._sessions() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._engine.dispose()


def _to_contractor(row: ContractorRow) -> Contractor:
    return Contractor(
        id=row.id,
        anon_name=row.anon_name,
        categories=row.categories,
        city=row.city,
        city_imputed=row.city_imputed,
        synthetic=row.synthetic,
        price_from_kzt=row.price_from_kzt,
        price_imputed=row.price_imputed,
        event_formats=row.event_formats,
        languages=row.languages,
        max_hours=row.max_hours,
        busy_dates=row.busy_dates,
        description=row.description,
    )

