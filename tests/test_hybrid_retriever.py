import numpy as np

from src.models import EvidenceChunk
from src.retriever import HybridEvidenceRetriever


class FakeEmbedder:
    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            lower = text.lower()
            if "encrypt" in lower or "cryptograph" in lower:
                vectors.append([1.0, 0.0])
            elif "training" in lower or "awareness" in lower:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.1, 0.1])
        return np.asarray(vectors, dtype=float)


def test_hybrid_retrieval_uses_semantic_signal():
    chunks = [
        EvidenceChunk(chunk_id="a", source_name="security.txt", text="AES encryption protects stored customer records."),
        EvidenceChunk(chunk_id="b", source_name="training.txt", text="Staff complete annual security awareness training."),
    ]
    retriever = HybridEvidenceRetriever(chunks, embedder=FakeEmbedder())
    matches = retriever.retrieve_query("cryptographic protection of data", top_k=1)
    assert retriever.mode == "hybrid"
    assert matches[0].chunk_id == "a"
    assert matches[0].retrieval_method == "hybrid_rrf"
    assert matches[0].semantic_score is not None


def test_hybrid_retriever_falls_back_safely_when_embedding_fails():
    class BrokenEmbedder:
        def embed(self, texts):
            raise RuntimeError("provider unavailable")

    chunks = [EvidenceChunk(chunk_id="a", source_name="ir.txt", text="Incident response exercises are conducted annually.")]
    retriever = HybridEvidenceRetriever(chunks, embedder=BrokenEmbedder())
    matches = retriever.retrieve_query("incident response", top_k=1)
    assert retriever.mode == "lexical_fallback"
    assert matches and matches[0].chunk_id == "a"
    assert retriever.semantic_error
