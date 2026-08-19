from src.models import AssessmentResult, AssessmentStatus, Control, Framework, FrameworkSource
from src.report import build_executive_html, priority_gaps_dataframe
from src.scoring import calculate_score


def make_framework():
    source = FrameworkSource(
        authority="Authority",
        title="Framework",
        version="1",
        source_url="https://example.test/framework",
        last_verified="2026-08-19",
    )
    controls = [
        Control(control_id="A", reference="1", title="Critical gap", requirement_summary="x", weight=2.0, source_locator="1", verification_status="verified"),
        Control(control_id="B", reference="2", title="Partial", requirement_summary="x", weight=1.0, source_locator="2", verification_status="verified"),
    ]
    return Framework(framework_id="fw", name="Test Framework", jurisdiction="Test", version="1", authority="Authority", source=source, scope_note="test", controls=controls)


def test_priority_gap_queue_orders_critical_first():
    fw = make_framework()
    results = [
        AssessmentResult(control_id="A", framework_id="fw", status=AssessmentStatus.NOT_EVIDENCED, rationale="missing"),
        AssessmentResult(control_id="B", framework_id="fw", status=AssessmentStatus.PARTIAL, rationale="partial"),
    ]
    bundle = {"fw": {"framework": fw, "results": results, "score": calculate_score(fw.controls, results)}}
    gaps = priority_gaps_dataframe(bundle)
    assert gaps.iloc[0]["priority"] == "Critical"
    assert "Critical gap" in gaps.iloc[0]["control"]


def test_executive_html_contains_readiness_notice():
    fw = make_framework()
    results = [AssessmentResult(control_id="A", framework_id="fw", status=AssessmentStatus.NOT_EVIDENCED, rationale="missing"), AssessmentResult(control_id="B", framework_id="fw", status=AssessmentStatus.PARTIAL, rationale="partial")]
    bundle = {"fw": {"framework": fw, "results": results, "score": calculate_score(fw.controls, results)}}
    html = build_executive_html(bundle, "Example Ltd")
    assert "Example Ltd" in html
    assert "not a legal-compliance determination" in html
    assert "Priority gaps" in html
    assert "Potential evidence reuse" in html
    assert "Type" in html


def test_review_required_is_not_mislabeled_as_confirmed_gap():
    fw = make_framework()
    results = [
        AssessmentResult(control_id="A", framework_id="fw", status=AssessmentStatus.REVIEW_REQUIRED, rationale="needs review"),
        AssessmentResult(control_id="B", framework_id="fw", status=AssessmentStatus.REVIEW_REQUIRED, rationale="needs review"),
    ]
    bundle = {"fw": {"framework": fw, "results": results, "score": calculate_score(fw.controls, results)}}
    gaps = priority_gaps_dataframe(bundle)
    assert set(gaps["priority"]) == {"Review"}
