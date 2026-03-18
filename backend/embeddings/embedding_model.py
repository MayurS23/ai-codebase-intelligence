"""
embedding_model.py — Thin wrapper around embedding providers.

Supports OpenAI text-embedding-3-small (default) with a local fallback
using a simple TF-IDF bag-of-words approach (no GPU needed, works offline).

Design: program to the EmbeddingModel interface so callers never care
which backend is running.
"""
from __future__ import annotations
import hashlib
import math
from collections import Counter
from typing import Protocol

from backend.config import get_settings

settings = get_settings()


class EmbeddingModel(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...


# ── OpenAI implementation ─────────────────────────────────────────────────── #
class OpenAIEmbeddingModel:
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # OpenAI recommends replacing newlines
        cleaned = [t.replace("\n", " ") for t in texts]
        response = self._client.embeddings.create(
            input=cleaned,
            model=self._model,
        )
        return [item.embedding for item in response.data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


# ── Local TF-IDF fallback (no API key needed) ─────────────────────────────── #
class LocalEmbeddingModel:
    """
    Simple TF-IDF based embeddings using a fixed vocabulary.
    Dimension: 512. Not great quality but totally offline.
    Use only for development / testing without API keys.
    """
    DIM = 512

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._tfidf_vector(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._tfidf_vector(text)

    def _tfidf_vector(self, text: str) -> list[float]:
        tokens = text.lower().split()
        tf = Counter(tokens)
        vec = [0.0] * self.DIM
        for token, count in tf.items():
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.DIM
            vec[idx] += count / max(len(tokens), 1)
        # L2 normalise
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


# ── Factory ───────────────────────────────────────────────────────────────── #
def get_embedding_model() -> EmbeddingModel:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingModel()
    return LocalEmbeddingModel()
