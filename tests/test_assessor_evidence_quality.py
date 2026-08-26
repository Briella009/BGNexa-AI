from types import SimpleNamespace

import src.assessor as assessor
from src.llm import LLMStatus
from src.models import AssessmentStatus, Control, EvidenceMatch, EvidenceType, FreshnessStatus


def control_with_operational_expectation():
    return Control(
        control_id="C1",
        reference="1",
        title="Quarterly access review",
        requirement_summary="Review privileged access quarterly and retain evidence.",
        evidence_examples=["quarterly access review reports", "approval records", "remediation tickets"],
        source_locator="1",
        verification_status="verified",
    )


def test_supported_ai_decision_is_capped_when_only_policy_intent_is_retrieved(monkeypatch):
    monkeypatch.setattr(assessor, "can_use_llm", lambda: True)
    monkeypatch.setattr(
        assessor,
        "assess_with_llm",
        lambda control, evidence: SimpleNamespace(
            status=LLMStatus.SUPPORTED,
            rationale="The policy requires quarterly reviews.",
            recommendation=None,
            evidence_strength="strong",
        ),
    )
    match = EvidenceMatch(
        chunk_id="p:0:0",
        source_name="access_policy.txt",
        excerpt="Quarterly access reviews are required.",
        retrieval_score=0.8,
        evidence_type=EvidenceType.DOCUMENTED_INTENT,
        freshness_status=FreshnessStatus.CURRENT,
        quality_flags=["documented_intent"],
    )
    result = assessor.assess_control("fw", control_with_operational_expectation(), [match], use_ai=True)
    assert result.status == AssessmentStatus.PARTIAL
    assert "intent_only_for_operational_requirement" in result.evidence_quality_flags
    assert "guardrail" in result.rationale.lower()


def test_supported_ai_decision_is_capped_when_all_evidence_is_stale(monkeypatch):
    monkeypatch.setattr(assessor, "can_use_llm", lambda: True)
    monkeypatch.setattr(
        assessor,
        "assess_with_llm",
        lambda control, evidence: SimpleNamespace(
            status=LLMStatus.SUPPORTED,
            rationale="The report records completed reviews.",
            recommendation=None,
            evidence_strength="strong",
        ),
    )
    match = EvidenceMatch(
        chunk_id="r:0:0",
        source_name="access_review_report.txt",
        excerpt="Completed quarterly access review records.",
        retrieval_score=0.9,
        evidence_type=EvidenceType.OPERATIONAL_RECORD,
        document_date="2022-01-01",
        age_days=1698,
        freshness_status=FreshnessStatus.STALE,
        quality_flags=["stale_evidence"],
    )
    result = assessor.assess_control("fw", control_with_operational_expectation(), [match], use_ai=True)
    assert result.status == AssessmentStatus.PARTIAL
    assert "stale_only_support" in result.evidence_quality_flags
