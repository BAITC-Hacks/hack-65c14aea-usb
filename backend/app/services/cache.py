import hashlib
import json
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse


class RecommendationCache(Protocol):
    async def get(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse | None:
        ...

    async def set(
        self,
        request: RecommendationRequest,
        response: RecommendationResponse,
    ) -> None:
        ...

    async def clear(self) -> None:
        ...

    async def ping(self) -> bool:
        ...

    async def close(self) -> None:
        ...


class RedisRecommendationCache:
    def __init__(self, settings: Settings) -> None:
        self._client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=settings.cache_request_timeout,
            socket_timeout=settings.cache_request_timeout,
        )
        self._ttl = settings.cache_ttl_seconds

    async def get(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse | None:
        try:
            payload = await self._client.get(cache_key(request))
            return RecommendationResponse.model_validate_json(payload) if payload else None
        except (RedisError, ValueError):
            return None

    async def set(
        self,
        request: RecommendationRequest,
        response: RecommendationResponse,
    ) -> None:
        try:
            await self._client.set(
                cache_key(request),
                response.model_dump_json(),
                ex=self._ttl,
            )
        except RedisError:
            return None

    async def clear(self) -> None:
        await self._client.flushdb()

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except RedisError:
            return False

    async def close(self) -> None:
        await self._client.aclose()


class NullRecommendationCache:
    async def get(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse | None:
        return None

    async def set(
        self,
        request: RecommendationRequest,
        response: RecommendationResponse,
    ) -> None:
        return None

    async def clear(self) -> None:
        return None

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class MemoryRecommendationCache(NullRecommendationCache):
    def __init__(self) -> None:
        self._values: dict[str, RecommendationResponse] = {}

    async def get(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse | None:
        return self._values.get(cache_key(request))

    async def set(
        self,
        request: RecommendationRequest,
        response: RecommendationResponse,
    ) -> None:
        self._values[cache_key(request)] = response

    async def clear(self) -> None:
        self._values.clear()


def cache_key(request: RecommendationRequest) -> str:
    canonical = json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"recommendations:v1:{digest}"

