from datetime import date
from pathlib import Path

import pytest

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.cache import MemoryRecommendationCache, cache_key
from scripts.import_dataset import read_csv_dataset

DATASET = Path("data/hackathon-dataset-anonymized.csv")


def test_real_csv_contains_expected_profiles() -> None:
    contractors = read_csv_dataset(DATASET)

    assert len(contractors) == 66
    assert len({item.id for item in contractors}) == 66
    assert sum(item.synthetic for item in contractors) == 13
    assert {item.city for item in contractors} == {"Алматы", "Астана", "Зарубежье"}
    assert sum(item.max_hours is None for item in contractors) == 9


@pytest.mark.asyncio
async def test_memory_cache_reuses_canonical_request_key() -> None:
    cache = MemoryRecommendationCache()
    request = RecommendationRequest(
        city="Алматы",
        event_date=date(2026, 11, 14),
        event_format="свадьба",
        category="Фотограф",
        budget_kzt=300_000,
    )
    response = RecommendationResponse.model_validate(
        {
            "status": "category_not_found",
            "items": [],
            "message": "test",
            "meta": {
                "total_in_city_category": 0,
                "eligible_count": 0,
                "exclusions": {},
            },
        }
    )

    await cache.set(request, response)

    assert await cache.get(request) == response
    assert cache_key(request) == cache_key(request.model_copy())
    await cache.clear()
    assert await cache.get(request) is None

