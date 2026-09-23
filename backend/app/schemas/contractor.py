from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.text import unique_strings


class Contractor(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1)
    anon_name: str = Field(min_length=1)
    categories: list[str] = Field(min_length=1)
    city: str = Field(min_length=1)
    price_from_kzt: int = Field(ge=0)
    event_formats: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    max_hours: float | None = Field(default=None, ge=0)
    busy_dates: list[date] = Field(default_factory=list)
    description: str = ""
    synthetic: bool = False
    city_imputed: bool = False
    price_imputed: bool = False
    search_relevance: float = Field(default=0, ge=0, exclude=True)
    semantic_relevance: float = Field(default=0, ge=0, le=1, exclude=True)
    semantic_evidence: str | None = Field(default=None, exclude=True)

    @field_validator("categories", "event_formats", "languages")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        cleaned = unique_strings(values)
        if not cleaned:
            raise ValueError("list must contain at least one non-empty value")
        return cleaned

    @field_validator("busy_dates")
    @classmethod
    def unique_busy_dates(cls, values: list[date]) -> list[date]:
        return sorted(set(values))

