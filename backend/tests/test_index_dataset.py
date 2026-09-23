import json

import pytest

from scripts.index_dataset import index_definition, read_dataset


def test_read_dataset_rejects_duplicate_ids(tmp_path) -> None:
    profile = {
        "id": "duplicate",
        "anon_name": "Профиль",
        "categories": ["Фотограф"],
        "city": "Алматы",
        "price_from_kzt": 100000,
        "event_formats": ["свадьба"],
        "languages": ["русский"],
        "max_hours": 8,
        "busy_dates": [],
        "description": "",
        "synthetic": False,
        "city_imputed": False,
        "price_imputed": False,
    }
    dataset = tmp_path / "profiles.jsonl"
    dataset.write_text(
        json.dumps(profile, ensure_ascii=False) + "\n"
        + json.dumps(profile, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate contractor id"):
        read_dataset(dataset)


def test_index_uses_one_shard_and_russian_analyzer() -> None:
    definition = index_definition()
    assert definition["settings"]["number_of_shards"] == 1
    assert definition["mappings"]["properties"]["description"]["analyzer"] == "russian"
