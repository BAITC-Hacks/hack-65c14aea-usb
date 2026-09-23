import re
from collections.abc import Iterable

WORD_RE = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)
STOP_WORDS = {
    "и", "в", "во", "на", "для", "с", "со", "по", "из", "от", "до",
    "а", "но", "или", "это", "мы", "вы", "ваш", "наш", "при",
}


def normalize_text(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold().replace("ё", "е")))


def tokenize(value: str) -> set[str]:
    return {token for token in normalize_text(value).split() if len(token) > 1 and token not in STOP_WORDS}


def unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = raw_value.strip()
        key = normalize_text(value)
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result

