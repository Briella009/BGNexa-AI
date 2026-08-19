from src.models import AssessmentResult, AssessmentStatus, EvidenceMatch
from src.review import apply_human_validation, build_assessment_snapshot, verify_snapshot_digest


def result_with_evidence():
    return AssessmentResult(
        control_id="C1",
        framework_id="fw",
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale="Candidate evidence found",
        evidence=[EvidenceMatch(chunk_id="x", source_name="policy.txt", excerpt="MFA is required.", retrieval_score=0.8)],
        requires_human_review=True,
    )


def test_supported_human_validation_requires_explicit_evidence_confirmation():
    result = result_with_evidence()
    try:
        apply_human_validation(result, AssessmentStatus.SUPPORTED, "Reviewer", "Evidence is direct.", False)
    except ValueError as exc:
        assert "explicitly confirm" in str(exc)
    else:
        raise AssertionError("Supported validation should require evidence confirmation")


def test_human_validation_resolves_review_and_records_reviewer():
    result = result_with_evidence()
    updated, validation = apply_human_validation(
        result,
        AssessmentStatus.SUPPORTED,
        "Ada Reviewer",
        "Verified the policy statement and scope.",
        True,
        reviewed_at="2026-08-19T00:00:00+00:00",
    )
    assert updated.status == AssessmentStatus.SUPPORTED
    assert updated.human_validated is True
    assert updated.requires_human_review is False
    assert updated.reviewer == "Ada Reviewer"
    assert validation.original_status == AssessmentStatus.REVIEW_REQUIRED


def test_human_review_cannot_override_applicability_to_not_applicable():
    result = result_with_evidence()
    try:
        apply_human_validation(result, AssessmentStatus.NOT_APPLICABLE, "Reviewer", "Out of scope", True)
    except ValueError as exc:
        assert "organisation profile" in str(exc)
    else:
        raise AssertionError("Applicability must not be overridden by the evidence reviewer")


def test_snapshot_digest_detects_tampering():
    class Obj:
        pass

    framework = Obj()
    framework.framework_id = "fw"
    framework.name = "Test Framework"
    framework.version = "1"
    framework.authority = "Test Authority"
    framework.source = Obj()
    framework.source.source_url = "https://example.test"
    framework.source.last_verified = "2026-08-19"

    bundle = {"fw": {"framework": framework, "results": [result_with_evidence()]}}
    snapshot = build_assessment_snapshot(
        bundle,
        organisation_profile={"organisation_name": "Test"},
        created_at="2026-08-19T00:00:00+00:00",
    )
    assert verify_snapshot_digest(snapshot)
    snapshot["organisation_profile"]["organisation_name"] = "Tampered"
    assert not verify_snapshot_digest(snapshot)
