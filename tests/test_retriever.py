from pathlib import Path

from src.evidence import parse_path
from src.framework_loader import load_frameworks
from src.retriever import EvidenceRetriever


ROOT = Path(__file__).resolve().parents[1]


def test_privacy_policy_retrieves_for_dpia():
    chunks = parse_path(ROOT / "sample_data" / "privacy_governance.txt")
    fw = load_frameworks(ROOT / "frameworks")["ndpa-2023"]
    control = next(c for c in fw.controls if c.control_id == "NDPA-28")
    matches = EvidenceRetriever(chunks).retrieve(control)
    assert matches
    assert "Impact Assessment" in matches[0].excerpt or "high risk" in matches[0].excerpt
