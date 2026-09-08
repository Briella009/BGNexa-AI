import pandas as pd

from src.assurance import (
    AssuranceTestResult,
    AssuranceWorkflowStatus,
    FindingSeverity,
    assurance_dataframe,
    build_assurance_snapshot,
    build_assurance_workplan,
    diff_workplan_events,
    evidence_request_dataframe,
    findings_dataframe,
    verify_assurance_snapshot,
    workspace_fingerprint,
)
from src.models import AssessmentResult, AssessmentStatus, Control, EvidenceMatch, Framework, FrameworkSource


def _bundle(status=AssessmentStatus.NOT_EVIDENCED, weight=2.0):
    source = FrameworkSource(
        authority="Example Authority",
        title="Example",
        version="1",
        source_url="https://example.com",
        last_verified="2026-09-08",
    )
    control = Control(
        control_id="C1",
        reference="1.1",
        title="Incident response exercise",
        requirement_summary="Perform and document incident response exercises.",
        evidence_examples=["exercise report", "lessons learned register"],
        capability_tags=["incident_response"],
        weight=weight,
        source_locator="1.1",
        verification_status="verified",
    )
    framework = Framework(
        framework_id="fw",
        name="Example Framework",
        jurisdiction="global",
        version="1",
        authority="Example Authority",
        source=source,
        scope_note="test",
        controls=[control],
    )
    result = AssessmentResult(
        control_id="C1",
        framework_id="fw",
        status=status,
        rationale="Current evidence is incomplete.",
        evidence=[
            EvidenceMatch(
                chunk_id="e:0:0",
                source_name="exercise.txt",
                excerpt="Exercise scheduled.",
                retrieval_score=0.8,
                source_hash="abc123",
            )
        ],
        recommendation="Obtain completed exercise evidence.",
        evidence_strength="weak",
        requires_human_review=True,
    )
    return {"fw": {"framework": framework, "results": [result], "score": None}}


def test_workplan_keeps_applicable_controls_and_does_not_auto_create_findings():
    workplan = build_assurance_workplan(_bundle())
    assert len(workplan) == 1
    item = workplan[0]
    assert item.priority == "Critical"
    assert item.workflow_status == AssuranceWorkflowStatus.OPEN
    assert item.test_result == AssuranceTestResult.NOT_TESTED
    assert item.finding_severity == FindingSeverity.NONE
    assert "exercise report" in item.evidence_request.lower()


def test_supported_result_becomes_validation_task_not_gap():
    workplan = build_assurance_workplan(_bundle(status=AssessmentStatus.SUPPORTED, weight=1.0))
    assert workplan[0].priority == "Validate"
    assert "independent validation" in workplan[0].evidence_request.lower()


def test_not_applicable_controls_are_excluded():
    assert build_assurance_workplan(_bundle(status=AssessmentStatus.NOT_APPLICABLE)) == []


def test_request_register_excludes_closed_items_and_findings_require_user_input():
    df = assurance_dataframe(build_assurance_workplan(_bundle()))
    assert len(evidence_request_dataframe(df)) == 1
    assert findings_dataframe(df).empty

    df.loc[0, "workflow_status"] = AssuranceWorkflowStatus.CLOSED.value
    assert evidence_request_dataframe(df).empty
    df.loc[0, "finding_title"] = "Exercise evidence unavailable"
    df.loc[0, "finding_severity"] = FindingSeverity.HIGH.value
    assert len(findings_dataframe(df)) == 1


def test_diff_events_records_editable_changes_only():
    before = assurance_dataframe(build_assurance_workplan(_bundle()))
    after = before.copy()
    after.loc[0, "control_owner"] = "Security Operations"
    after.loc[0, "workflow_status"] = AssuranceWorkflowStatus.UNDER_REVIEW.value
    after.loc[0, "framework_name"] = "Do not log read-only change"
    events = diff_workplan_events(before, after, "Tester")
    assert {event["field"] for event in events} == {"control_owner", "workflow_status"}
    assert all(event["actor"] == "Tester" for event in events)


def test_assurance_snapshot_is_tamper_evident_and_links_assessment_fingerprint():
    bundle = _bundle()
    df = assurance_dataframe(build_assurance_workplan(bundle))
    fingerprint = workspace_fingerprint(bundle)
    snapshot = build_assurance_snapshot(
        df,
        metadata={"engagement_title": "Test"},
        assessment_fingerprint=fingerprint,
        assessment_sha256="readiness123",
        created_at="2026-09-08T12:00:00+00:00",
    )
    assert snapshot["assessment_fingerprint"] == fingerprint
    assert verify_assurance_snapshot(snapshot)

    tampered = dict(snapshot)
    tampered["metadata"] = {"engagement_title": "Changed"}
    assert not verify_assurance_snapshot(tampered)
