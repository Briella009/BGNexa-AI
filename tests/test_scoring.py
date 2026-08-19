from src.models import AssessmentResult, AssessmentStatus, Control
from src.scoring import calculate_score


def control(cid: str, weight: float = 1.0) -> Control:
    return Control(
        control_id=cid,
        reference=cid,
        title=cid,
        requirement_summary="Requirement",
        evidence_examples=[],
        capability_tags=[],
        weight=weight,
        source_locator="test",
        verification_status="test",
    )


def result(cid: str, status: AssessmentStatus) -> AssessmentResult:
    return AssessmentResult(
        control_id=cid,
        framework_id="test",
        status=status,
        rationale="Test rationale",
        evidence=[],
        requires_human_review=True,
    )


def test_review_required_does_not_inflate_resolved_readiness():
    controls = [control("A"), control("B"), control("C")]
    results = [
        result("A", AssessmentStatus.SUPPORTED),
        result("B", AssessmentStatus.NOT_EVIDENCED),
        result("C", AssessmentStatus.REVIEW_REQUIRED),
    ]
    score = calculate_score(controls, results)
    assert score.provisional_readiness_percent == 50.0
    assert score.coverage_percent == 66.7
    assert score.review_required == 1


def test_not_applicable_is_excluded_from_applicable_weight():
    controls = [control("A", 2.0), control("B", 1.0)]
    results = [
        result("A", AssessmentStatus.SUPPORTED),
        result("B", AssessmentStatus.NOT_APPLICABLE),
    ]
    score = calculate_score(controls, results)
    assert score.provisional_readiness_percent == 100.0
    assert score.coverage_percent == 100.0
    assert score.applicable_weight == 2.0
