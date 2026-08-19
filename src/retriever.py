from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .embeddings import Embedder
from .models import Control, EvidenceChunk, EvidenceMatch


def _control_query(control: Control) -> str:
    return " ".join([control.title, control.requirement_summary, *control.evidence_examples, *control.capability_tags])


def _safe_cosine(query_vector: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.asarray([], dtype=float)
    q = np.asarray(query_vector, dtype=float).reshape(1, -1)
    m = np.asarray(matrix, dtype=float)
    q_norm = np.linalg.norm(q, axis=1, keepdims=True)
    m_norm = np.linalg.norm(m, axis=1, keepdims=True)
    q_norm[q_norm == 0] = 1.0
    m_norm[m_norm == 0] = 1.0
    return ((q / q_norm) @ (m / m_norm).T)[0]


@dataclass
class EvidenceRetriever:
    """Deterministic lexical baseline used when embeddings are unavailable."""

    chunks: list[EvidenceChunk]
    min_score: float = 0.05

    def __post_init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self.matrix = None
        if self.chunks:
            self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])

    def retrieve(self, control: Control, top_k: int = 4) -> list[EvidenceMatch]:
        return self.retrieve_query(_control_query(control), top_k=top_k)

    def retrieve_query(self, query: str, top_k: int = 4) -> list[EvidenceMatch]:
        if not self.chunks or self.matrix is None or not query.strip():
            return []

        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.matrix)[0]
        ranked = scores.argsort()[::-1][:top_k]

        matches: list[EvidenceMatch] = []
        for idx in ranked:
            score = float(scores[idx])
            if score < self.min_score:
                continue
            chunk = self.chunks[int(idx)]
            matches.append(
                EvidenceMatch(
                    chunk_id=chunk.chunk_id,
                    source_name=chunk.source_name,
                    page=chunk.page,
                    excerpt=chunk.text[:900],
                    retrieval_score=round(score, 4),
                    lexical_score=round(score, 4),
                    retrieval_method="tfidf",
                    injection_flag=chunk.injection_flag,
                    content_hash=chunk.content_hash,
                )
            )
        return matches


@dataclass
class HybridEvidenceRetriever:
    """Hybrid lexical + embedding retrieval using reciprocal-rank fusion.

    RRF avoids pretending TF-IDF cosine scores and embedding cosine scores are on
    the same calibration scale. If the semantic provider is unavailable, the
    retriever degrades safely to the lexical baseline.
    """

    chunks: list[EvidenceChunk]
    embedder: Embedder | None = None
    min_lexical_score: float = 0.03
    rrf_k: int = 60
    lexical_weight: float = 0.45
    semantic_weight: float = 0.55

    def __post_init__(self) -> None:
        self.lexical = EvidenceRetriever(self.chunks, min_score=0.0)
        self.semantic_matrix: np.ndarray | None = None
        self.semantic_error: str | None = None
        if self.embedder is not None and self.chunks:
            try:
                self.semantic_matrix = self.embedder.embed([c.text for c in self.chunks])
                if len(self.semantic_matrix) != len(self.chunks):
                    raise ValueError("Embedding provider returned a different number of vectors than input chunks")
            except Exception as exc:  # safe fallback; surfaced in UI metadata
                self.semantic_error = f"{type(exc).__name__}: {exc}"
                self.semantic_matrix = None

    @property
    def mode(self) -> str:
        return "hybrid" if self.semantic_matrix is not None else "lexical_fallback"

    def retrieve(self, control: Control, top_k: int = 4) -> list[EvidenceMatch]:
        return self.retrieve_query(_control_query(control), top_k=top_k)

    def retrieve_query(self, query: str, top_k: int = 4) -> list[EvidenceMatch]:
        if not self.chunks or not query.strip():
            return []

        # Rank a wider pool before fusing.
        pool = max(top_k * 4, 12)
        lexical_matches = self.lexical.retrieve_query(query, top_k=min(pool, len(self.chunks)))
        lexical_score_by_id = {m.chunk_id: m.lexical_score or 0.0 for m in lexical_matches}
        lexical_rank = {m.chunk_id: rank for rank, m in enumerate(lexical_matches, start=1)}

        semantic_score_by_id: dict[str, float] = {}
        semantic_rank: dict[str, int] = {}
        if self.semantic_matrix is not None and self.embedder is not None:
            try:
                q_vec = self.embedder.embed([query])
                scores = _safe_cosine(q_vec[0], self.semantic_matrix)
                ranked = scores.argsort()[::-1][: min(pool, len(self.chunks))]
                for rank, idx in enumerate(ranked, start=1):
                    chunk_id = self.chunks[int(idx)].chunk_id
                    semantic_rank[chunk_id] = rank
                    semantic_score_by_id[chunk_id] = float(scores[int(idx)])
            except Exception as exc:
                self.semantic_error = f"{type(exc).__name__}: {exc}"

        if not semantic_rank:
            return [m for m in lexical_matches if (m.lexical_score or 0.0) >= self.min_lexical_score][:top_k]

        all_ids = set(lexical_rank) | set(semantic_rank)
        fused: list[tuple[str, float]] = []
        for chunk_id in all_ids:
            score = 0.0
            if chunk_id in lexical_rank:
                score += self.lexical_weight / (self.rrf_k + lexical_rank[chunk_id])
            if chunk_id in semantic_rank:
                score += self.semantic_weight / (self.rrf_k + semantic_rank[chunk_id])
            fused.append((chunk_id, score))
        fused.sort(key=lambda item: item[1], reverse=True)

        max_score = fused[0][1] if fused else 1.0
        chunks_by_id = {c.chunk_id: c for c in self.chunks}
        matches: list[EvidenceMatch] = []
        for chunk_id, fused_score in fused[:top_k]:
            chunk = chunks_by_id[chunk_id]
            normalized = fused_score / max_score if max_score else 0.0
            matches.append(
                EvidenceMatch(
                    chunk_id=chunk.chunk_id,
                    source_name=chunk.source_name,
                    page=chunk.page,
                    excerpt=chunk.text[:900],
                    retrieval_score=round(normalized, 4),
                    lexical_score=round(lexical_score_by_id.get(chunk_id, 0.0), 4),
                    semantic_score=round(semantic_score_by_id.get(chunk_id, 0.0), 4),
                    retrieval_method="hybrid_rrf",
                    injection_flag=chunk.injection_flag,
                    content_hash=chunk.content_hash,
                )
            )
        return matches
