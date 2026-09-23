import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import Settings, get_settings
from app.repositories.base import ContractorRepository
from app.repositories.hybrid import HybridContractorRepository
from app.services.cache import (
    NullRecommendationCache,
    RecommendationCache,
    RedisRecommendationCache,
)


def create_app(
    repository: ContractorRepository | None = None,
    cache: RecommendationCache | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active_repository = repository or HybridContractorRepository(app_settings)
        active_cache = cache or (
            NullRecommendationCache()
            if repository is not None
            else RedisRecommendationCache(app_settings)
        )
        app.state.repository = active_repository
        app.state.cache = active_cache
        try:
            yield
        finally:
            await asyncio.gather(
                active_repository.close(),
                active_cache.close(),
                return_exceptions=True,
            )

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready(request: Request) -> JSONResponse:
        repository_ready, cache_ready = await asyncio.gather(
            request.app.state.repository.ping(),
            request.app.state.cache.ping(),
        )
        is_ready = repository_ready and cache_ready
        code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            status_code=code,
            content={
                "status": "ready" if is_ready else "not_ready",
                "dependencies": {
                    "catalog": repository_ready,
                    "cache": cache_ready,
                },
            },
        )

    return app


app = create_app()

