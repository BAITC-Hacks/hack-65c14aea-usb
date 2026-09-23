import re
from datetime import date

from app.core.text import tokenize
from app.schemas.contractor import Contractor
from app.schemas.recommendation import RecommendationRequest

MONTHS = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def description_relevance(
    contractor: Contractor,
    request: RecommendationRequest,
) -> tuple[float, str | None]:
    query_parts = [request.category, request.event_format]
    if request.language:
        query_parts.append(request.language)
    query_tokens = tokenize(" ".join(query_parts))
    sentences = [
        sentence.strip()
        for sentence in SENTENCE_RE.split(contractor.description.strip())
        if sentence.strip()
    ]
    if not sentences:
        return 0.0, None
    if not query_tokens:
        return 0.0, shorten_sentence(sentences[0])

    best_overlap = 0
    # Keep a concrete profile fact even when its wording does not overlap with
    # the request. It makes equally priced candidates distinguishable.
    best_sentence = sentences[0]
    for sentence in sentences:
        overlap = len(query_tokens & tokenize(sentence))
        if overlap > best_overlap:
            best_overlap = overlap
            best_sentence = sentence

    relevance = best_overlap / len(query_tokens)
    return relevance, shorten_sentence(best_sentence)


def shorten_sentence(sentence: str) -> str:
    if len(sentence) <= 110:
        return sentence
    return sentence[:107].rstrip() + "…"


def build_explanation(
    contractor: Contractor,
    request: RecommendationRequest,
    description_evidence: str | None,
) -> str:
    event_date = format_date(request.event_date)
    budget_gap = request.budget_kzt - contractor.price_from_kzt
    if budget_gap == 0:
        price_fact = "стартовая цена точно совпадает с бюджетом"
    else:
        price_fact = (
            f"стартовая цена {format_money(contractor.price_from_kzt)} ₸ "
            f"укладывается в бюджет с запасом {format_money(budget_gap)} ₸"
        )
    first_sentence = f"Свободен {event_date}; {price_fact}."

    factors = [f"Берёт формат «{request.event_format}»"]
    if request.language:
        factors.append(f"работает на языке «{request.language}»")
    if request.duration_hours is not None:
        if contractor.max_hours is None:
            factors.append("услуга не ограничена временем присутствия")
        else:
            factors.append(
                f"доступен до {format_hours(contractor.max_hours)}, "
                f"что покрывает запрос на {format_hours(request.duration_hours)}"
            )
    if description_evidence:
        factors.append(f"в описании указано: «{description_evidence.rstrip('.!?')}»")

    second_sentence = "; ".join(factors)
    return first_sentence + " " + second_sentence[0].upper() + second_sentence[1:] + "."


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month]} {value.year}"


def format_money(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def format_hours(value: float) -> str:
    if value.is_integer():
        return f"{int(value)} ч"
    return f"{value:g} ч"

