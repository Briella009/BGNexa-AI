from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

import pandas as pd
from pydantic import BaseModel, Field

from .evidence_quality import control_requires_operational_evidence
from .models import AssessmentResult, AssessmentStatus, Control, Framework


class AssuranceWorkflowStatus(str, Enum):
    OPEN = "open"
    EVIDENCE_REQUESTED = "evidence_requested"
    UNDER_REVIEW = "under_review"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    READY_FOR_RETEST = "ready_for_retest"
    CLOSED = "closed"
    RISK_ACCEPTED = "risk_accepted"


class AssuranceTestResult(str, Enum):
    NOT_TESTED = "not_tested"
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    INCONCLUSIVE = "inconclusive"


class FindingSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AssuranceWorkItem(BaseModel):
    work_item_id: str
    framework_id: str
    framework_name: str
    framework_type: str
    control_id: str
    reference: str
    control_title: str
    source_locator: str
    assessment_status: str
    human_validated: bool = False
    priority: str
    weight: float
    evidence_strength: str
    evidence_sources: list[str] = Field(default_factory=list)
    evidence_hashes: list[str] = Field(default_factory=list)
    evidence_quality_flags: list[str] = Field(default_factory=list)
    assessment_rationale: str = ""
    recommendation: str = ""
    test_objective: str
    suggested_test_procedure: str
    evidence_request: str
    control_owner: str = ""
    assurance_owner: str = ""
    due_date: str = ""
    workflow_status: AssuranceWorkflowStatus = AssuranceWorkflowStatus.OPEN
    test_result: AssuranceTestResult = AssuranceTestResult.NOT_TESTED
    sample_reference: str = ""
    finding_title: str = ""
    finding_severity: FindingSeverity = FindingSeverity.NONE
    management_response: str = ""
    action_owner: str = ""
    target_date: str = ""
    reviewer: str = ""
    reviewer_note: str = ""
    closure_evidence: str = ""


_EDITABLE_FIELDS = [
    "control_owner",
    "assurance_owner",
    "due_date",
    "workflow_status",
    "test_result",
    "sample_reference",
    "finding_title",
    "finding_severity",
    "management_response",
    "action_owner",
    "target_date",
    "reviewer",
    "reviewer_note",
    "closure_evidence",
]


_PRIORITY_RANK = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Review": 4,
    "Validate": 5,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _work_item_id(framework_id: str, control_id: str) -> str:
    digest = hashlib.sha256(f"{framework_id}|{control_id}".encode("utf-8")).hexdigest()[:12]
    return f"AWP-{digest.upper()}"


def assurance_priority(result: AssessmentResult, weight: float) -> str:
    """Prioritise assurance work without pretending the value is a risk rating."""

    if result.status == AssessmentStatus.NOT_EVIDENCED and weight >= 1.8:
        return "Critical"
    if result.status == AssessmentStatus.NOT_EVIDENCED:
        return "High"
    if result.status == AssessmentStatus.PARTIAL and weight >= 1.5:
        return "High"
    if result.status == AssessmentStatus.PARTIAL:
        return "Medium"
    if result.status == AssessmentStatus.REVIEW_REQUIRED:
        return "Review"
    return "Validate"


def _evidence_request(control: Control, result: AssessmentResult) -> str:
    examples = [item.strip() for item in control.evidence_examples if item.strip()][:5]
    if examples:
        requested = "; ".join(examples)
        base = f"Provide current, scope-relevant evidence such as: {requested}."
    else:
        base = f"Provide current evidence that directly demonstrates: {control.requirement_summary}"

    if result.status == AssessmentStatus.SUPPORTED:
        return base + " Provide enough detail for independent validation of the existing supported assessment."
    if result.status == AssessmentStatus.PARTIAL:
        return base + " Focus on the implementation elements not yet evidenced by the current assessment."
    if result.status == AssessmentStatus.NOT_EVIDENCED:
        return base + " No sufficient evidence is currently recorded for this requirement."
    return base + " The current assessment requires qualified human review before conclusion."


def _test_procedure(control: Control) -> str:
    if control_requires_operational_evidence(control):
        return (
            "Inspect the control design and cited evidence; select a risk-based sample from the assessment period where appropriate; "
            "verify execution, approval, timeliness, exception handling and traceability; reconcile exceptions to remediation records; "
            "record the sample basis and conclusion. Do not infer operating effectiveness from policy text alone."
        )
    return (
        "Inspect the documented control design, ownership, approval, scope and current version; corroborate the documented requirement "
        "with available implementation evidence where relevant; record exceptions, evidence references and the reviewer conclusion."
    )


def _test_objective(control: Control) -> str:
    return f"Determine whether the available evidence is sufficient to support the assessed readiness outcome for {control.reference} - {control.title}."


def _control_map(framework: Framework) -> dict[str, Control]:
    return {control.control_id: control for control in framework.controls}


def build_assurance_workplan(bundle: dict[str, dict[str, Any]]) -> list[AssuranceWorkItem]:
    """Turn the current readiness assessment into an auditable assurance/GRC workplan.

    Every applicable control is retained. Supported controls become validation tasks;
    unresolved or gap states become review/remediation tasks. ``not_applicable`` controls
    stay outside the workplan because applicability is controlled elsewhere.
    """

    work_items: list[AssuranceWorkItem] = []
    for item in bundle.values():
        framework: Framework = item["framework"]
        controls = _control_map(framework)
        for result in item["results"]:
            if result.status == AssessmentStatus.NOT_APPLICABLE:
                continue
            control = controls[result.control_id]
            sources = sorted({match.source_name for match in result.evidence})
            source_hashes = sorted({match.source_hash for match in result.evidence if match.source_hash})
            work_items.append(
                AssuranceWorkItem(
                    work_item_id=_work_item_id(framework.framework_id, control.control_id),
                    framework_id=framework.framework_id,
                    framework_name=framework.name,
                    framework_type=framework.framework_type,
                    control_id=control.control_id,
                    reference=control.reference,
                    control_title=control.title,
                    source_locator=control.source_locator,
                    assessment_status=result.status.value,
                    human_validated=result.human_validated,
                    priority=assurance_priority(result, control.weight),
                    weight=control.weight,
                    evidence_strength=result.evidence_strength,
                    evidence_sources=sources,
                    evidence_hashes=source_hashes,
                    evidence_quality_flags=list(result.evidence_quality_flags),
                    assessment_rationale=result.rationale,
                    recommendation=result.recommendation or "",
                    test_objective=_test_objective(control),
                    suggested_test_procedure=_test_procedure(control),
                    evidence_request=_evidence_request(control, result),
                )
            )

    return sorted(
        work_items,
        key=lambda row: (
            _PRIORITY_RANK.get(row.priority, 99),
            -row.weight,
            row.framework_name.lower(),
            row.reference.lower(),
        ),
    )


def assurance_dataframe(work_items: Iterable[AssuranceWorkItem]) -> pd.DataFrame:
    rows = []
    for item in work_items:
        data = item.model_dump(mode="json")
        data["evidence_sources"] = "; ".join(data["evidence_sources"])
        data["evidence_hashes"] = "; ".join(data["evidence_hashes"])
        data["evidence_quality_flags"] = "; ".join(data["evidence_quality_flags"])
        rows.append(data)
    return pd.DataFrame(rows)


def evidence_request_dataframe(workplan: pd.DataFrame) -> pd.DataFrame:
    if workplan.empty:
        return pd.DataFrame(
            columns=[
                "work_item_id",
                "priority",
                "framework_name",
                "reference",
                "control_title",
                "control_owner",
                "due_date",
                "evidence_request",
                "workflow_status",
            ]
        )
    columns = [
        "work_item_id",
        "priority",
        "framework_name",
        "reference",
        "control_title",
        "control_owner",
        "due_date",
        "evidence_request",
        "workflow_status",
    ]
    return workplan.loc[workplan["workflow_status"].astype(str) != AssuranceWorkflowStatus.CLOSED.value, columns].reset_index(drop=True)


def findings_dataframe(workplan: pd.DataFrame) -> pd.DataFrame:
    if workplan.empty:
        return workplan.copy()
    severity = workplan["finding_severity"].fillna("none").astype(str)
    response = workplan["management_response"].fillna("").astype(str).str.strip()
    finding = workplan["finding_title"].fillna("").astype(str).str.strip()
    mask = (severity != FindingSeverity.NONE.value) | response.ne("") | finding.ne("")
    columns = [
        "work_item_id",
        "priority",
        "framework_name",
        "reference",
        "control_title",
        "finding_title",
        "finding_severity",
        "management_response",
        "action_owner",
        "target_date",
        "workflow_status",
        "test_result",
        "reviewer",
        "reviewer_note",
        "closure_evidence",
    ]
    return workplan.loc[mask, columns].reset_index(drop=True)


def workspace_fingerprint(bundle: dict[str, dict[str, Any]]) -> str:
    rows: list[dict[str, Any]] = []
    for framework_id in sorted(bundle):
        item = bundle[framework_id]
        for result in sorted(item["results"], key=lambda r: r.control_id):
            rows.append(
                {
                    "framework_id": framework_id,
                    "control_id": result.control_id,
                    "status": result.status.value,
                    "human_validated": result.human_validated,
                    "reviewed_at": result.reviewed_at,
                    "evidence_hashes": sorted({e.source_hash for e in result.evidence if e.source_hash}),
                }
            )
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalise_cell(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return str(value)


def diff_workplan_events(previous: pd.DataFrame, current: pd.DataFrame, actor: str) -> list[dict[str, str]]:
    """Create an append-only session audit trail for edited assurance fields."""

    if previous.empty or current.empty or "work_item_id" not in previous or "work_item_id" not in current:
        return []
    actor = actor.strip() or "unspecified user"
    previous_rows = previous.set_index("work_item_id", drop=False)
    current_rows = current.set_index("work_item_id", drop=False)
    events: list[dict[str, str]] = []
    event_time = utc_now_iso()

    for work_item_id in sorted(set(previous_rows.index) & set(current_rows.index)):
        before = previous_rows.loc[work_item_id]
        after = current_rows.loc[work_item_id]
        for field in _EDITABLE_FIELDS:
            if field not in previous.columns or field not in current.columns:
                continue
            before_value = _normalise_cell(before[field])
            after_value = _normalise_cell(after[field])
            if before_value == after_value:
                continue
            event_id = hashlib.sha256(
                f"{event_time}|{work_item_id}|{field}|{before_value}|{after_value}".encode("utf-8")
            ).hexdigest()[:16]
            events.append(
                {
                    "event_id": event_id,
                    "timestamp": event_time,
                    "actor": actor,
                    "work_item_id": str(work_item_id),
                    "field": field,
                    "from": before_value,
                    "to": after_value,
                }
            )
    return events


def build_assurance_snapshot(
    workplan: pd.DataFrame,
    *,
    metadata: dict[str, Any] | None = None,
    assessment_fingerprint: str | None = None,
    assessment_sha256: str | None = None,
    audit_events: list[dict[str, Any]] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    created_at = created_at or utc_now_iso()
    metadata = metadata or {}
    audit_events = audit_events or []
    records = [] if workplan.empty else [
        {key: _normalise_cell(value) for key, value in row.items()}
        for row in workplan.to_dict(orient="records")
    ]
    payload = {
        "snapshot_schema": "bgnexa-assurance/v1",
        "created_at": created_at,
        "metadata": metadata,
        "assessment_fingerprint": assessment_fingerprint,
        "assessment_sha256": assessment_sha256,
        "work_items": records,
        "audit_events": audit_events,
        "notice": (
            "Assurance workpaper support only. This snapshot does not constitute an audit opinion, legal-compliance determination, "
            "certification decision, regulator approval, or proof of reviewer identity."
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {**payload, "sha256": digest}


def verify_assurance_snapshot(snapshot: dict[str, Any]) -> bool:
    supplied = snapshot.get("sha256")
    if not supplied:
        return False
    payload = {key: value for key, value in snapshot.items() if key != "sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest() == supplied


WORKFLOW_STATUS_OPTIONS = [status.value for status in AssuranceWorkflowStatus]
TEST_RESULT_OPTIONS = [status.value for status in AssuranceTestResult]
FINDING_SEVERITY_OPTIONS = [status.value for status in FindingSeverity]
