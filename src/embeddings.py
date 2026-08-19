from __future__ import annotations

import os
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    """Small interface used by hybrid retrieval and easily replaced in tests."""

    def embed(self, texts: list[str]) -> np.ndarray: ...


def can_use_openai_embeddings() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


class OpenAIEmbedder:
    """OpenAI embeddings adapter.

    The import is intentionally lazy so the offline lexical path works even when
    the OpenAI SDK is not installed in the execution environment.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=float)
        if not can_use_openai_embeddings():
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(model=self.model, input=texts)
        vectors = [item.embedding for item in response.data]
        return np.asarray(vectors, dtype=float)
