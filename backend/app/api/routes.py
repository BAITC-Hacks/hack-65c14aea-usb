from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.repositories.base import ContractorRepository, RepositoryUnavailableError
from app.schemas.recommendation import (
    CatalogOptions,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.cache import RecommendationCache
from app.services.recommendations import RecommendationService

api_router = APIRouter(prefix="/api/v1")


def get_repository(request: Request) -> ContractorRepository:
    return request.app.state.repository


def get_cache(request: Request) -> RecommendationCache:
    return request.app.state.cache


@api_router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(
    payload: RecommendationRequest,
    repository: ContractorRepository = Depends(get_repository),
    cache: RecommendationCache = Depends(get_cache),
) -> RecommendationResponse:
    cached = await cache.get(payload)
    if cached is not None:
        return cached
    try:
        response = await RecommendationService(repository).recommend(payload)
    except RepositoryUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Каталог подрядчиков временно недоступен.",
        ) from exc
    await cache.set(payload, response)
    return response


@api_router.get("/catalog/options", response_model=CatalogOptions)
async def catalog_options(
    repository: ContractorRepository = Depends(get_repository),
) -> CatalogOptions:
    try:
        return await repository.catalog_options()
    except RepositoryUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Каталог подрядчиков временно недоступен.",
        ) from exc

