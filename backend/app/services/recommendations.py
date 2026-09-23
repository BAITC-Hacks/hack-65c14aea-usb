from dataclasses import dataclass
from enum import StrEnum

from app.core.text import normalize_text
from app.repositories.base import ContractorRepository
from app.schemas.contractor import Contractor
from app.schemas.recommendation import (
    ExclusionSummary,
    RecommendationItem,
    RecommendationMeta,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationStatus,
)
from app.services.explanations import build_explanation, description_relevance


class ExclusionReason(StrEnum):
    BUSY = "busy"
    OVER_BUDGET = "over_budget"
    WRONG_FORMAT = "wrong_format"
    WRONG_LANGUAGE = "wrong_language"
    INSUFFICIENT_DURATION = "insufficient_duration"


@dataclass(frozen=True)
class RankedCandidate:
    contractor: Contractor
    score: float
    description_evidence: str | None


class RecommendationService:
    def __init__(self, repository: ContractorRepository) -> None:
        self._repository = repository

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        search_text = " ".join(
            value for value in (request.category, request.event_format, request.language) if value
        )
        candidates = await self._repository.list_by_city_and_category(
            request.city,
            request.category,
            search_text,
        )
        if not candidates:
            return RecommendationResponse(
                status=RecommendationStatus.CATEGORY_NOT_FOUND,
                items=[],
                message=(
                    f"В городе «{request.city}» нет подрядчиков "
                    f"категории «{request.category}»."
                ),
                meta=RecommendationMeta(
                    total_in_city_category=0,
                    eligible_count=0,
                    exclusions=ExclusionSummary(),
                ),
            )

        exclusions = ExclusionSummary()
        eligible: list[RankedCandidate] = []
        for contractor in candidates:
            reasons = exclusion_reasons(contractor, request)
            for reason in reasons:
                setattr(exclusions, reason.value, getattr(exclusions, reason.value) + 1)
            if not reasons:
                lexical_relevance, evidence = description_relevance(contractor, request)
                hybrid_relevance = min(max(contractor.search_relevance, 0.0), 1.0)
                eligible.append(
                    RankedCandidate(
                        contractor=contractor,
                        score=score_candidate(
                            contractor,
                            request,
                            max(
                                lexical_relevance,
                                hybrid_relevance,
                                contractor.semantic_relevance,
                            ),
                        ),
                        description_evidence=contractor.semantic_evidence or evidence,
                    )
                )

        meta = RecommendationMeta(
            total_in_city_category=len(candidates),
            eligible_count=len(eligible),
            exclusions=exclusions,
        )
        if not eligible:
            return RecommendationResponse(
                status=RecommendationStatus.NO_ELIGIBLE_CANDIDATES,
                items=[],
                message=no_candidates_message(len(candidates), exclusions),
                meta=meta,
            )

        ranked = sorted(
            eligible,
            key=lambda item: (-item.score, normalize_text(item.contractor.id)),
        )
        selected = ranked[:3]
        items = [
            RecommendationItem(
                id=item.contractor.id,
                name=item.contractor.anon_name,
                categories=item.contractor.categories,
                city=item.contractor.city,
                price_from_kzt=item.contractor.price_from_kzt,
                synthetic=item.contractor.synthetic,
                explanation=build_explanation(
                    item.contractor,
                    request,
                    item.description_evidence,
                ),
            )
            for item in selected
        ]
        return RecommendationResponse(
            status=RecommendationStatus.MATCHED,
            items=items,
            message=matched_message(len(eligible), len(candidates), exclusions),
            meta=meta,
        )


def exclusion_reasons(
    contractor: Contractor,
    request: RecommendationRequest,
) -> set[ExclusionReason]:
    reasons: set[ExclusionReason] = set()
    if request.event_date in contractor.busy_dates:
        reasons.add(ExclusionReason.BUSY)
    if contractor.price_from_kzt > request.budget_kzt:
        reasons.add(ExclusionReason.OVER_BUDGET)
    if normalize_text(request.event_format) not in {
        normalize_text(value) for value in contractor.event_formats
    }:
        reasons.add(ExclusionReason.WRONG_FORMAT)
    if request.language and normalize_text(request.language) not in {
        normalize_text(value) for value in contractor.languages
    }:
        reasons.add(ExclusionReason.WRONG_LANGUAGE)
    if (
        request.duration_hours is not None
        and contractor.max_hours is not None
        and contractor.max_hours < request.duration_hours
    ):
        reasons.add(ExclusionReason.INSUFFICIENT_DURATION)
    return reasons


def score_candidate(
    contractor: Contractor,
    request: RecommendationRequest,
    description_score: float,
) -> float:
    budget_headroom = 1 - contractor.price_from_kzt / request.budget_kzt
    score = max(0.0, budget_headroom) * 35
    score += 25  # event format is a hard filter
    if request.language:
        score += 15
    if request.duration_hours is not None:
        score += 10
    score += min(max(description_score, 0.0), 1.0) * 15
    return round(score, 6)


def no_candidates_message(total: int, exclusions: ExclusionSummary) -> str:
    reasons = exclusion_phrases(exclusions)
    details = "; ".join(reasons) if reasons else "не прошли обязательные условия"
    return (
        f"В городе и категории найдено профилей: {total}, "
        f"но подходящих нет: {details}."
    )


def matched_message(
    eligible_count: int,
    total: int,
    exclusions: ExclusionSummary,
) -> str:
    if eligible_count >= 3:
        return f"Подобраны 3 из {eligible_count} подходящих подрядчиков."
    excluded = total - eligible_count
    if excluded == 0:
        return (
            f"Подходящих подрядчиков только {eligible_count}: "
            "в этом городе и категории больше профилей нет."
        )
    details = "; ".join(exclusion_phrases(exclusions))
    return (
        f"Подходящих подрядчиков только {eligible_count} из {total}: "
        f"{details or 'остальные не прошли обязательные условия'}."
    )


def exclusion_phrases(exclusions: ExclusionSummary) -> list[str]:
    values = (
        (exclusions.busy, "заняты на выбранную дату"),
        (exclusions.over_budget, "превышают бюджет"),
        (exclusions.wrong_format, "не берут выбранный формат"),
        (exclusions.wrong_language, "не работают на выбранном языке"),
        (exclusions.insufficient_duration, "не покрывают нужную длительность"),
    )
    return [f"{count} — {label}" for count, label in values if count]

