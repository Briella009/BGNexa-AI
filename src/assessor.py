from __future__ import annotations

from .llm import assess_with_llm, can_use_llm
from .models import AssessmentResult, AssessmentStatus, Control, EvidenceMatch


def assess_control(framework_id: str, control: Control, matches: list[EvidenceMatch], use_ai: bool) -> AssessmentResult:
    if not matches:
        return AssessmentResult(
            control_id=control.control_id,
            framework_id=framework_id,
            status=AssessmentStatus.NOT_EVIDENCED,
            rationale="No relevant evidence candidate was retrieved from the uploaded documents.",
            evidence=[],
            recommendation="Provide or create evidence that directly addresses this requirement, then perform human review.",
            evidence_strength="none",
            ai_assessed=False,
            requires_human_review=True,
        )

    if any(m.injection_flag for m in matches):
        return AssessmentResult(
            control_id=control.control_id,
            framework_id=framework_id,
            status=AssessmentStatus.REVIEW_REQUIRED,
            rationale="At least one retrieved passage resembles prompt-injection content. It was treated as untrusted data and blocked from automated evidence judgement.",
            evidence=matches,
            recommendation="Inspect the flagged source manually and remove or quarantine malicious/instruction-like content before reassessment.",
            evidence_strength="weak",
            ai_assessed=False,
            requires_human_review=True,
        )

    if use_ai and can_use_llm():
        decision = assess_with_llm(control, matches)
        return AssessmentResult(
            control_id=control.control_id,
            framework_id=framework_id,
            status=AssessmentStatus(decision.status.value),
            rationale=decision.rationale,
            evidence=matches,
            recommendation=decision.recommendation,
            evidence_strength=decision.evidence_strength,
            ai_assessed=True,
            requires_human_review=True,
        )

    return AssessmentResult(
        control_id=control.control_id,
        framework_id=framework_id,
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale="Relevant evidence candidates were found. Confirm that they explicitly demonstrate the requirement before resolving this control.",
        evidence=matches,
        recommendation="Review the cited evidence and set the final status to supported, partially supported, or not evidenced.",
        evidence_strength="weak",
        ai_assessed=False,
        requires_human_review=True,
    )
