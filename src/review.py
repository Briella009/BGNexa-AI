from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .models import AssessmentResult, AssessmentStatus, Framework, HumanValidation


REVIEWABLE_STATUSES = {
    AssessmentStatus.SUPPORTED,
    AssessmentStatus.PARTIAL,
    AssessmentStatus.NOT_EVIDENCED,
    AssessmentStatus.REVIEW_REQUIRED,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_human_decision(
    result: AssessmentResult,
    validated_status: AssessmentStatus,
    reviewer: str,
    note: str,
    evidence_confirmed: bool,
) -> None:
    if validated_status not in REVIEWABLE_STATUSES:
        raise ValueError("Human review cannot override applicability to not_applicable; update the organisation profile instead.")
    if not reviewer.strip():
        raise ValueError("Reviewer name is required for a validated decision.")
    if not note.strip():
        raise ValueError("A reviewer note is required to preserve the rationale for the override.")
    if validated_status in {AssessmentStatus.SUPPORTED, AssessmentStatus.PARTIAL}:
        if not result.evidence:
            raise ValueError("Supported/partial decisions require at least one cited evidence candidate.")
        if not evidence_confirmed:
            raise ValueError("The reviewer must explicitly confirm the cited evidence before resolving as supported/partial.")


def apply_human_validation(
    result: AssessmentResult,
    validated_status: AssessmentStatus,
    reviewer: str,
    note: str,
    evidence_confirmed: bool,
    reviewed_at: str | None = None,
) -> tuple[AssessmentResult, HumanValidation]:
    validate_human_decision(result, validated_status, reviewer, note, evidence_confirmed)
    reviewed_at = reviewed_at or utc_now_iso()

    validation = HumanValidation(
        control_id=result.control_id,
        framework_id=result.framework_id,
        original_status=result.status,
        validated_status=validated_status.value,
        reviewer=reviewer.strip(),
        note=note.strip(),
        evidence_confirmed=evidence_confirmed,
        reviewed_at=reviewed_at,
    )

    updated = result.model_copy(
        update={
            "status": validated_status,
            "requires_human_review": validated_status == AssessmentStatus.REVIEW_REQUIRED,
            "human_validated": validated_status != AssessmentStatus.REVIEW_REQUIRED,
            "reviewer": reviewer.strip(),
            "reviewer_note": note.strip(),
            "reviewed_at": reviewed_at,
        }
    )
    return updated, validation


def build_assessment_snapshot(
    bundle: dict[str, dict[str, Any]],
    organisation_profile: dict[str, Any],
    validations: list[HumanValidation] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Create a deterministic, tamper-evident assessment snapshot.

    The digest is not a digital signature and does not prove reviewer identity.
    It does make accidental or undisclosed content changes detectable.
    """
    created_at = created_at or utc_now_iso()
    validations = validations or []

    frameworks: list[dict[str, Any]] = []
    for framework_id in sorted(bundle):
        item = bundle[framework_id]
        framework: Framework = item["framework"]
        frameworks.append(
            {
                "framework_id": framework.framework_id,
                "name": framework.name,
                "version": framework.version,
                "authority": framework.authority,
                "framework_type": getattr(framework, "framework_type", "framework"),
                "source_url": framework.source.source_url,
                "source_type": getattr(framework.source, "source_type", "official"),
                "source_last_verified": framework.source.last_verified,
                "score": item["score"].model_dump(mode="json") if item.get("score") is not None else None,
                "controls": [
                    {
                        "control_id": result.control_id,
                        "status": result.status.value,
                        "rationale": result.rationale,
                        "evidence_strength": result.evidence_strength,
                        "evidence_quality_flags": result.evidence_quality_flags,
                        "evidence_quality_note": result.evidence_quality_note,
                        "evidence": [
                            {
                                "chunk_id": e.chunk_id,
                                "source_name": e.source_name,
                                "page": e.page,
                                "content_hash": e.content_hash,
                                "retrieval_method": e.retrieval_method,
                                "evidence_type": e.evidence_type.value,
                                "document_date": e.document_date,
                                "date_source": e.date_source,
                                "age_days": e.age_days,
                                "freshness_status": e.freshness_status.value,
                                "quality_flags": e.quality_flags,
                            }
                            for e in result.evidence
                        ],
                        "ai_assessed": result.ai_assessed,
                        "human_validated": result.human_validated,
                        "reviewer": result.reviewer,
                        "reviewed_at": result.reviewed_at,
                    }
                    for result in item["results"]
                ],
            }
        )

    payload = {
        "snapshot_schema": "readiness-copilot/v2",
        "created_at": created_at,
        "organisation_profile": deepcopy(organisation_profile),
        "frameworks": frameworks,
        "validations": [v.model_dump(mode="json") for v in validations],
        "notice": (
            "Evidence-backed readiness snapshot only; not a legal-compliance determination, "
            "ISO certification, regulator approval, or audit opinion."
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {**payload, "sha256": digest}


def verify_snapshot_digest(snapshot: dict[str, Any]) -> bool:
    supplied = snapshot.get("sha256")
    if not supplied:
        return False
    payload = {k: v for k, v in snapshot.items() if k != "sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest() == supplied
