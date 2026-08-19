from __future__ import annotations

from .models import AssessmentResult, AssessmentStatus, Control, ScoreSummary


STATUS_VALUE = {
    AssessmentStatus.SUPPORTED: 1.0,
    AssessmentStatus.PARTIAL: 0.5,
    AssessmentStatus.NOT_EVIDENCED: 0.0,
}


def calculate_score(controls: list[Control], results: list[AssessmentResult]) -> ScoreSummary:
    control_by_id = {c.control_id: c for c in controls}
    applicable_weight = 0.0
    resolved_weight = 0.0
    earned = 0.0

    counts = {status: 0 for status in AssessmentStatus}

    for result in results:
        counts[result.status] += 1
        control = control_by_id[result.control_id]

        if result.status == AssessmentStatus.NOT_APPLICABLE:
            continue

        applicable_weight += control.weight
        if result.status in STATUS_VALUE:
            resolved_weight += control.weight
            earned += control.weight * STATUS_VALUE[result.status]

    readiness = round((earned / resolved_weight) * 100, 1) if resolved_weight else None
    coverage = round((resolved_weight / applicable_weight) * 100, 1) if applicable_weight else 0.0

    return ScoreSummary(
        provisional_readiness_percent=readiness,
        resolved_weight=round(resolved_weight, 2),
        applicable_weight=round(applicable_weight, 2),
        coverage_percent=coverage,
        supported=counts[AssessmentStatus.SUPPORTED],
        partial=counts[AssessmentStatus.PARTIAL],
        not_evidenced=counts[AssessmentStatus.NOT_EVIDENCED],
        review_required=counts[AssessmentStatus.REVIEW_REQUIRED],
        not_applicable=counts[AssessmentStatus.NOT_APPLICABLE],
    )
