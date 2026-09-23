from datetime import date

import pytest

from app.repositories.memory import MemoryContractorRepository
from app.schemas.contractor import Contractor


@pytest.fixture
def contractors() -> list[Contractor]:
    return [
        Contractor(
            id="photo-a",
            anon_name="Профиль А",
            categories=["Фотограф"],
            city="Алматы",
            price_from_kzt=100_000,
            event_formats=["свадьба", "корпоратив"],
            languages=["русский", "казахский"],
            max_hours=8,
            busy_dates=[date(2026, 11, 15)],
            description="Репортажная съёмка казахских свадеб. Передаёт фотографии за 7 дней.",
        ),
        Contractor(
            id="photo-b",
            anon_name="Профиль Б",
            categories=["Фотограф"],
            city="Алматы",
            price_from_kzt=150_000,
            event_formats=["свадьба"],
            languages=["русский"],
            max_hours=6,
            busy_dates=[],
            description="Специализируется на студийных портретах и свадебной съёмке.",
        ),
        Contractor(
            id="photo-c",
            anon_name="Профиль В",
            categories=["Фотограф"],
            city="Алматы",
            price_from_kzt=90_000,
            event_formats=["свадьба"],
            languages=["русский"],
            max_hours=10,
            busy_dates=[date(2026, 11, 14)],
            description="Фотографирует свадьбы и юбилеи.",
        ),
        Contractor(
            id="decor-null-hours",
            anon_name="Профиль Г",
            categories=["Декоратор"],
            city="Алматы",
            price_from_kzt=80_000,
            event_formats=["свадьба"],
            languages=["русский"],
            max_hours=None,
            busy_dates=[],
            description="Оформление свадеб цветами и текстилем.",
            synthetic=True,
        ),
        Contractor(
            id="photo-astana",
            anon_name="Профиль Д",
            categories=["Фотограф"],
            city="Астана",
            price_from_kzt=70_000,
            event_formats=["свадьба"],
            languages=["русский"],
            max_hours=8,
            busy_dates=[],
            description="Свадебный фотограф в Астане.",
        ),
    ]


@pytest.fixture
def repository(contractors: list[Contractor]) -> MemoryContractorRepository:
    return MemoryContractorRepository(contractors)

