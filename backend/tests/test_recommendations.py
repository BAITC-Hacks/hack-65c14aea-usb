from datetime import date

import pytest

from app.repositories.memory import MemoryContractorRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationStatus
from app.services.recommendations import RecommendationService


def request_for(**overrides: object) -> RecommendationRequest:
    data: dict[str, object] = {
        "city": "Алматы",
        "event_date": date(2026, 11, 14),
        "event_format": "свадьба",
        "category": "Фотограф",
        "budget_kzt": 200_000,
        "duration_hours": 6,
        "language": "русский",
    }
    data.update(overrides)
    return RecommendationRequest.model_validate(data)


@pytest.mark.asyncio
async def test_busy_contractor_is_excluded_and_shortage_is_explained(repository) -> None:
    response = await RecommendationService(repository).recommend(request_for())

    assert response.status == RecommendationStatus.MATCHED
    assert [item.id for item in response.items] == ["photo-a", "photo-b"]
    assert "photo-c" not in {item.id for item in response.items}
    assert response.meta.exclusions.busy == 1
    assert "заняты" in response.message
    assert all("Свободен 14 ноября 2026" in item.explanation for item in response.items)


@pytest.mark.asyncio
async def test_same_request_has_same_order(repository) -> None:
    service = RecommendationService(repository)
    first = await service.recommend(request_for())
    second = await service.recommend(request_for())

    assert [item.id for item in first.items] == [item.id for item in second.items]


@pytest.mark.asyncio
async def test_different_date_changes_results(repository) -> None:
    service = RecommendationService(repository)
    november_14 = await service.recommend(request_for())
    november_15 = await service.recommend(
        request_for(event_date=date(2026, 11, 15))
    )

    assert [item.id for item in november_14.items] != [
        item.id for item in november_15.items
    ]
    assert "photo-a" not in {item.id for item in november_15.items}
    assert "Свободен 15 ноября 2026" in november_15.items[0].explanation


@pytest.mark.asyncio
async def test_category_not_found_is_distinct(repository) -> None:
    response = await RecommendationService(repository).recommend(
        request_for(category="Отель")
    )

    assert response.status == RecommendationStatus.CATEGORY_NOT_FOUND
    assert response.items == []
    assert response.meta.total_in_city_category == 0


@pytest.mark.asyncio
async def test_candidates_exist_but_none_are_eligible(repository) -> None:
    response = await RecommendationService(repository).recommend(
        request_for(budget_kzt=10_000)
    )

    assert response.status == RecommendationStatus.NO_ELIGIBLE_CANDIDATES
    assert response.items == []
    assert response.meta.total_in_city_category == 3
    assert response.meta.exclusions.over_budget == 3
    assert "превышают бюджет" in response.message


@pytest.mark.asyncio
async def test_null_max_hours_is_not_rejected(repository) -> None:
    response = await RecommendationService(repository).recommend(
        request_for(category="Декоратор", duration_hours=12)
    )

    assert response.status == RecommendationStatus.MATCHED
    assert response.items[0].id == "decor-null-hours"
    assert response.items[0].synthetic is True
    assert "не ограничена временем присутствия" in response.items[0].explanation


@pytest.mark.asyncio
async def test_explanations_are_specific(repository) -> None:
    response = await RecommendationService(repository).recommend(request_for())

    explanations = {
        item.explanation.replace(item.name, "") for item in response.items
    }
    assert len(explanations) == len(response.items)


@pytest.mark.asyncio
async def test_description_relevance_affects_ranking(contractors) -> None:
    enriched = [
        contractor.model_copy(
            update={
                "search_relevance": 100.0 if contractor.id == "photo-b" else 0.0
            }
        )
        for contractor in contractors
    ]
    repository = MemoryContractorRepository(enriched)

    response = await RecommendationService(repository).recommend(request_for())

    assert [item.id for item in response.items[:2]] == ["photo-b", "photo-a"]
