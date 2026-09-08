from __future__ import annotations

from .evidence_quality import assessment_quality_guardrails, evidence_quality_summary
from .llm import LLMTemporarilyUnavailable, assess_with_llm, can_use_llm
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
            evidence_quality_flags=["no_evidence_retrieved"],
            evidence_quality_note="No evidence quality assessment was possible because no candidate evidence was retrieved.",
            ai_assessed=False,
            requires_human_review=True,
        )

    quality_note = evidence_quality_summary(matches)
    inherited_flags = sorted({flag for match in matches for flag in match.quality_flags})

    if any(m.injection_flag for m in matches):
        return AssessmentResult(
            control_id=control.control_id,
            framework_id=framework_id,
            status=AssessmentStatus.REVIEW_REQUIRED,
            rationale="At least one retrieved passage resembles prompt-injection content. It was treated as untrusted data and blocked from automated evidence judgement.",
            evidence=matches,
            recommendation="Inspect the flagged source manually and remove or quarantine malicious/instruction-like content before reassessment.",
            evidence_strength="weak",
            evidence_quality_flags=sorted({*inherited_flags, "prompt_injection_block"}),
            evidence_quality_note=quality_note,
            ai_assessed=False,
            requires_human_review=True,
        )

    if use_ai and can_use_llm():
        try:
            decision = assess_with_llm(control, matches)
        except LLMTemporarilyUnavailable as exc:
            wait_note = (
                f" Provider cooldown: about {exc.retry_after_seconds}s."
                if exc.retry_after_seconds
                else ""
            )
            return AssessmentResult(
                control_id=control.control_id,
                framework_id=framework_id,
                status=AssessmentStatus.REVIEW_REQUIRED,
                rationale=(
                    "Relevant evidence candidates were found, but the external AI reviewer is temporarily unavailable. "
                    "BGNexa preserved the evidence and deferred the judgement to human review rather than retrying repeatedly."
                    + wait_note
                ),
                evidence=matches,
                recommendation="Review the cited evidence manually or retry AI review after the provider cooldown.",
                evidence_strength="weak",
                evidence_quality_flags=sorted({*inherited_flags, "ai_provider_temporarily_unavailable"}),
                evidence_quality_note=quality_note,
                ai_assessed=False,
                requires_human_review=True,
            )

        proposed_status = decision.status.value
        guarded_status, guard_flags, guard_note = assessment_quality_guardrails(control, matches, proposed_status)
        rationale = decision.rationale
        recommendation = decision.recommendation
        evidence_strength = decision.evidence_strength

        if guard_note:
            rationale = f"{rationale} BGNexa evidence-quality guardrail: {guard_note}"
            if recommendation:
                recommendation = f"{recommendation} Obtain fresher or implementation-level evidence before resolving as supported."
            else:
                recommendation = "Obtain fresher or implementation-level evidence before resolving as supported."
            if evidence_strength == "strong":
                evidence_strength = "moderate"

        return AssessmentResult(
            control_id=control.control_id,
            framework_id=framework_id,
            status=AssessmentStatus(guarded_status),
            rationale=rationale,
            evidence=matches,
            recommendation=recommendation,
            evidence_strength=evidence_strength,
            evidence_quality_flags=sorted({*inherited_flags, *guard_flags}),
            evidence_quality_note=quality_note,
            ai_assessed=True,
            requires_human_review=True,
        )

    manual_note = quality_note
    if "stale_evidence" in inherited_flags:
        manual_note += " Stale evidence should not be used by itself to establish current implementation."
    if "documented_intent" in inherited_flags:
        manual_note += " Policy/procedure evidence shows documented intent; implementation may require records, logs, tests, configurations or filings."

    return AssessmentResult(
        control_id=control.control_id,
        framework_id=framework_id,
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale="Relevant evidence candidates were found. Confirm that they explicitly demonstrate the requirement before resolving this control.",
        evidence=matches,
        recommendation="Review the cited evidence, its evidence type and freshness, then set the final status to supported, partially supported, or not evidenced.",
        evidence_strength="weak",
        evidence_quality_flags=inherited_flags,
        evidence_quality_note=manual_note,
        ai_assessed=False,
        requires_human_review=True,
    )
