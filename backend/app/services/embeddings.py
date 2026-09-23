import math
import re
import threading
from collections.abc import Sequence

from fastembed import TextEmbedding

from app.core.config import Settings
from app.schemas.contractor import Contractor

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
MAX_EVIDENCE_LENGTH = 150


class EmbeddingService:
    """Deterministic local multilingual embeddings backed by ONNX Runtime."""

    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self._model = TextEmbedding(
            model_name=settings.embedding_model,
            cache_dir=settings.embedding_cache_dir,
            threads=1,
        )
        self._lock = threading.Lock()
        self._vector_cache: dict[str, tuple[float, ...]] = {}

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        with self._lock:
            missing = list(
                dict.fromkeys(text for text in texts if text not in self._vector_cache)
            )
            if missing:
                raw_vectors = list(self._model.embed(missing, batch_size=8))
                for text, raw_vector in zip(missing, raw_vectors, strict=True):
                    self._vector_cache[text] = tuple(
                        _normalized(raw_vector.tolist())
                    )
            vectors = [list(self._vector_cache[text]) for text in texts]
        if any(len(vector) != self.dimensions for vector in vectors):
            raise RuntimeError(
                f"Embedding model {self.model_name!r} returned unexpected dimensions"
            )
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([query_embedding_text(text)])[0]

    def best_evidence_batch(
        self,
        descriptions: Sequence[str],
        query_vector: Sequence[float],
    ) -> list[tuple[float, str | None]]:
        groups = [split_sentences(description) for description in descriptions]
        sentences = [sentence for group in groups for sentence in group]
        if not sentences:
            return [(0.0, None) for _ in descriptions]

        vectors = self.embed_documents(sentences)
        results: list[tuple[float, str | None]] = []
        offset = 0
        for group in groups:
            if not group:
                results.append((0.0, None))
                continue
            group_vectors = vectors[offset : offset + len(group)]
            offset += len(group)
            scored = [
                (cosine_similarity(query_vector, vector), sentence)
                for sentence, vector in zip(group, group_vectors, strict=True)
            ]
            score, evidence = max(scored, key=lambda item: (item[0], item[1]))
            normalized_score = min(max((score + 1.0) / 2.0, 0.0), 1.0)
            results.append((normalized_score, shorten_evidence(evidence)))
        return results


def contractor_embedding_text(contractor: Contractor) -> str:
    return " ".join(
        (
            f"Категории: {', '.join(contractor.categories)}.",
            f"Форматы мероприятий: {', '.join(contractor.event_formats)}.",
            f"Языки работы: {', '.join(contractor.languages)}.",
            f"Описание профиля: {contractor.description or 'не заполнено'}.",
        )
    )


def query_embedding_text(text: str) -> str:
    return f"Запрос на event-подрядчика: {text}."


def split_sentences(description: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in SENTENCE_RE.split(description.strip())
        if sentence.strip()
    ]


def shorten_evidence(sentence: str) -> str:
    if len(sentence) <= MAX_EVIDENCE_LENGTH:
        return sentence
    shortened = sentence[: MAX_EVIDENCE_LENGTH - 1].rsplit(" ", 1)[0]
    return shortened.rstrip(" ,;:-") + "…"


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have equal dimensions")
    return sum(a * b for a, b in zip(left, right, strict=True))


def _normalized(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("Embedding model returned a zero vector")
    return [float(value / norm) for value in vector]
