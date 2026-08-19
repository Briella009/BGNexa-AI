from pathlib import Path

from src.evaluation import run_retrieval_evaluation, run_security_evaluation


ROOT = Path(__file__).resolve().parents[1]


def test_retrieval_golden_set_meets_stage3_quality_gate():
    result = run_retrieval_evaluation(
        frameworks_dir=ROOT / "frameworks",
        fixtures_dir=ROOT / "evals" / "fixtures",
        cases_path=ROOT / "evals" / "retrieval_cases.yaml",
    )

    assert result["cases"] >= 30
    assert result["recall_at_3"] >= 0.90
    assert result["mrr"] >= 0.75
    assert not result["failures"]


def test_security_evaluation_blocks_flagged_prompt_injection_context():
    result = run_security_evaluation(
        fixtures_dir=ROOT / "evals" / "fixtures",
        frameworks_dir=ROOT / "frameworks",
    )

    assert result["prompt_injection_detection"] is True
    assert result["copilot_flagged_evidence_exclusion"] is True
    assert result["pass"] is True
