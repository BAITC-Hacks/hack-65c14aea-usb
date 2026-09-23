from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

DATASET_DATE_FROM = date(2026, 9, 23)
DATASET_DATE_TO = date(2026, 12, 31)


class RecommendationStatus(StrEnum):
    MATCHED = "matched"
    CATEGORY_NOT_FOUND = "category_not_found"
    NO_ELIGIBLE_CANDIDATES = "no_eligible_candidates"


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    city: str = Field(min_length=1)
    event_date: date
    event_format: str = Field(min_length=1)
    category: str = Field(min_length=1)
    budget_kzt: int = Field(gt=0)
    duration_hours: float | None = Field(default=None, gt=0, le=24)
    language: str | None = Field(default=None, min_length=1)

    @field_validator("event_date")
    @classmethod
    def date_is_covered_by_dataset(cls, value: date) -> date:
        if not DATASET_DATE_FROM <= value <= DATASET_DATE_TO:
            raise ValueError(
                f"event_date must be between {DATASET_DATE_FROM.isoformat()} "
                f"and {DATASET_DATE_TO.isoformat()}"
            )
        return value


class ExclusionSummary(BaseModel):
    busy: int = 0
    over_budget: int = 0
    wrong_format: int = 0
    wrong_language: int = 0
    insufficient_duration: int = 0


class RecommendationMeta(BaseModel):
    total_in_city_category: int
    eligible_count: int
    exclusions: ExclusionSummary


class RecommendationItem(BaseModel):
    id: str
    name: str
    categories: list[str]
    city: str
    price_from_kzt: int
    synthetic: bool
    explanation: str


class RecommendationResponse(BaseModel):
    status: RecommendationStatus
    items: list[RecommendationItem] = Field(max_length=3)
    message: str
    meta: RecommendationMeta


class CatalogOptions(BaseModel):
    cities: list[str]
    categories: list[str]
    event_formats: list[str]
    languages: list[str]

