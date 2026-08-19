from pathlib import Path

from src.crosswalk import capability_crosswalk
from src.framework_loader import load_frameworks


ROOT = Path(__file__).resolve().parents[1]


def test_crosswalk_only_returns_multi_framework_capabilities():
    frameworks = load_frameworks(ROOT / "frameworks")
    selected = [frameworks["ndpa-2023"], frameworks["iso-iec-27001-2022-amd1-2024"]]
    rows = capability_crosswalk(selected)
    assert rows
    assert all(row["framework_count"] >= 2 for row in rows)
    assert all(row["control_count"] >= row["framework_count"] for row in rows)
    assert all("not a declaration of control equivalence" in row["note"] for row in rows)


def test_crosswalk_ranks_broadest_evidence_reuse_opportunities_first():
    frameworks = load_frameworks(ROOT / "frameworks")
    selected = [
        frameworks["ndpa-2023"],
        frameworks["cbn-dmb-psb-2024"],
        frameworks["nist-csf-2.0"],
        frameworks["gdpr-2016-679"],
    ]
    rows = capability_crosswalk(selected)
    assert rows
    counts = [(row["framework_count"], row["control_count"]) for row in rows]
    assert counts == sorted(counts, key=lambda x: (-x[0], -x[1]))
