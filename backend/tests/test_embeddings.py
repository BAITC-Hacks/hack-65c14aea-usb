import pytest

from app.schemas.contractor import Contractor
from app.services.embeddings import (
    contractor_embedding_text,
    cosine_similarity,
    query_embedding_text,
    shorten_evidence,
    split_sentences,
)


def test_embedding_text_contains_only_profile_facts() -> None:
    contractor = Contractor(
        id="profile-1",
        anon_name="Профиль",
        categories=["Фотограф"],
        city="Алматы",
        price_from_kzt=100_000,
        event_formats=["свадьба"],
        languages=["русский", "казахский"],
        max_hours=8,
        description="Снимаю живые эмоции и отдаю фотографии за семь дней.",
    )

    text = contractor_embedding_text(contractor)

    assert "Фотограф" in text
    assert "свадьба" in text
    assert "русский, казахский" in text
    assert contractor.description in text


def test_vector_helpers_are_deterministic() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert query_embedding_text("фотограф свадьба") == (
        "Запрос на event-подрядчика: фотограф свадьба."
    )
    assert split_sentences("Первый факт. Второй факт!") == [
        "Первый факт.",
        "Второй факт!",
    ]
    assert shorten_evidence("а" * 200).endswith("…")
