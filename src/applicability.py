from __future__ import annotations

from .models import AssessmentResult, AssessmentStatus, Control


def recommended_framework_ids(
    *,
    operates_in_nigeria: bool,
    cbn_regulated_type: str,
    include_iso: bool,
    include_nist: bool = False,
    include_gdpr: bool = False,
) -> list[str]:
    selected: list[str] = []

    if operates_in_nigeria:
        selected.extend(["ndpa-2023", "ndpc-gaid-2025"])

    if cbn_regulated_type == "DMB/PSB":
        selected.append("cbn-dmb-psb-2024")
    elif cbn_regulated_type == "OFI":
        selected.append("cbn-ofi-2022")

    if include_iso:
        selected.append("iso-iec-27001-2022-amd1-2024")
    if include_nist:
        selected.append("nist-csf-2.0")
    if include_gdpr:
        selected.append("gdpr-2016-679")

    return selected


def _review_result(
    *,
    framework_id: str,
    control: Control,
    rationale: str,
    recommendation: str,
) -> AssessmentResult:
    return AssessmentResult(
        control_id=control.control_id,
        framework_id=framework_id,
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale=rationale,
        evidence=[],
        recommendation=recommendation,
        evidence_strength="none",
        ai_assessed=False,
        requires_human_review=True,
    )


def _not_applicable_result(*, framework_id: str, control: Control, rationale: str) -> AssessmentResult:
    return AssessmentResult(
        control_id=control.control_id,
        framework_id=framework_id,
        status=AssessmentStatus.NOT_APPLICABLE,
        rationale=rationale,
        evidence=[],
        recommendation=None,
        evidence_strength="none",
        ai_assessed=False,
        requires_human_review=False,
    )


def resolve_control_applicability(
    *,
    framework_id: str,
    control: Control,
    dcpmi_status: str,
    processing_role: str,
    dcpmi_tier: str = "Unknown",
    registration_exempt_status: str = "Unknown",
    gdpr_scope_status: str = "Unknown",
    gdpr_dpo_required_status: str = "Unknown",
    gdpr_cross_border_transfer_status: str = "Unknown",
    gdpr_dpia_required_status: str = "Unknown",
    gdpr_ropa_required_status: str = "Unknown",
    gdpr_uses_processors_status: str = "Unknown",
) -> AssessmentResult | None:
    """Return a result only when applicability can be decided before evidence review.

    Legal/regulatory scope is not delegated to the LLM. Unknown or internally
    ambiguous applicability is surfaced as human review and therefore cannot
    inflate readiness.
    """
    rules = control.applicability or {}

    if rules.get("requires_gdpr_scope"):
        if gdpr_scope_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The organisation profile records a confirmed GDPR territorial-scope determination of No for the assessed processing scope.",
            )
        if gdpr_scope_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="GDPR territorial scope is unresolved. The AI is not allowed to determine Article 3 applicability.",
                recommendation="Document a qualified Article 3 territorial-scope determination before treating this GDPR requirement as applicable or not applicable.",
            )

        # Once GDPR territorial scope is confirmed, resolve explicit controller/processor
        # scope before checking conditional obligations such as RoPA, DPIA, DPO or
        # controller-side processor governance. This prevents a processor-only
        # organisation from being sent to review for a controller-only condition.
        gdpr_allowed_roles = rules.get("processing_roles")
        if gdpr_allowed_roles:
            if processing_role == "Unsure":
                return _review_result(
                    framework_id=framework_id,
                    control=control,
                    rationale="Applicability depends on whether the organisation acts as a controller, processor, or both for the assessed GDPR processing scope.",
                    recommendation="Confirm the organisation's GDPR processing role for the relevant processing activity.",
                )
            if processing_role not in gdpr_allowed_roles:
                return _not_applicable_result(
                    framework_id=framework_id,
                    control=control,
                    rationale=f"This GDPR control is scoped to processing role(s): {', '.join(gdpr_allowed_roles)}.",
                )

    if rules.get("requires_gdpr_ropa"):
        if gdpr_ropa_required_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The profile records a confirmed determination that the Article 30 record-of-processing obligation is not triggered for this processing scope.",
            )
        if gdpr_ropa_required_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Article 30 record-of-processing applicability is unresolved, including any Article 30(5) exception analysis.",
                recommendation="Document whether Article 30 record-keeping is required for this processing scope before assessing RoPA evidence.",
            )

    if rules.get("requires_gdpr_dpia"):
        if gdpr_dpia_required_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The profile records a confirmed determination that the assessed processing is not subject to a mandatory Article 35 DPIA.",
            )
        if gdpr_dpia_required_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Whether the assessed processing is likely to result in high risk and therefore requires an Article 35 DPIA has not been determined.",
                recommendation="Perform and document a DPIA-threshold assessment before treating the DPIA control as applicable or not applicable.",
            )

    if rules.get("requires_gdpr_controller_uses_processors"):
        if gdpr_uses_processors_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The profile records that the assessed controller processing scope does not use processors.",
            )
        if gdpr_uses_processors_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="It is not confirmed whether the controller uses processors for the assessed processing scope.",
                recommendation="Confirm processor relationships before assessing Article 28 controller-side processor governance.",
            )

    if rules.get("requires_gdpr_dpo"):
        if gdpr_dpo_required_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The profile records a confirmed determination that mandatory DPO designation is not triggered for this processing scope.",
            )
        if gdpr_dpo_required_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Mandatory DPO designation under GDPR Article 37 has not been determined.",
                recommendation="Confirm whether an Article 37 mandatory DPO trigger applies before assessing DPO-specific evidence.",
            )

    if rules.get("requires_gdpr_cross_border_transfer"):
        if gdpr_cross_border_transfer_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="The profile records that the assessed processing scope does not involve transfers to third countries or international organisations.",
            )
        if gdpr_cross_border_transfer_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="International-transfer applicability is unresolved for the assessed GDPR processing scope.",
                recommendation="Confirm whether personal data is transferred to a third country or international organisation and document the transfer mechanism where applicable.",
            )

    if rules.get("requires_dcpmi"):
        if dcpmi_status == "No":
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale="This control is scoped to a data controller/processor of major importance, and the profile is marked No.",
            )
        if dcpmi_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Applicability cannot be resolved until DCPMI status is determined against current NDPC designation guidance.",
                recommendation="Determine and document whether the organisation is a data controller or processor of major importance before assessing this requirement.",
            )

    # Registration exemptions in GAID Schedule 7 are framed for specified data
    # controllers of major importance. Do not generalise them to processor-only
    # or mixed roles without human review.
    if rules.get("registration_requirement") and dcpmi_status == "Yes":
        if registration_exempt_status == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Registration applicability is unresolved because the profile has not confirmed whether a current NDPC registration exemption applies.",
                recommendation="Confirm and document whether a Section 44 / GAID Schedule 7 registration exemption applies before assessing registration evidence.",
            )
        if registration_exempt_status == "Yes":
            if processing_role == "Controller":
                return _not_applicable_result(
                    framework_id=framework_id,
                    control=control,
                    rationale="The profile records a documented NDPC registration exemption for this data controller of major importance. Retain the exemption evidence outside this registration control.",
                )
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="A registration exemption is recorded, but GAID Schedule 7 frames the listed exemption categories for data controllers of major importance; this processing role is not controller-only.",
                recommendation="Obtain qualified confirmation of the registration position for the organisation's processor or mixed role and retain the supporting determination.",
            )

    tier_policy = rules.get("dcpmi_tier_policy")
    if tier_policy and dcpmi_status == "Yes":
        if dcpmi_tier == "Unknown":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="This requirement has tier-sensitive DCPMI applicability and the organisation's UHL/EHL/OHL tier is unknown.",
                recommendation="Confirm the organisation's current DCPMI tier against GAID 2025 Schedule 7 before assessing this requirement.",
            )
        if dcpmi_tier in tier_policy.get("review", []):
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale=rules.get(
                    "tier_review_rationale",
                    "The source material requires human review for this DCPMI tier before the control can be treated as applicable or not applicable.",
                ),
                recommendation=rules.get(
                    "tier_review_recommendation",
                    "Obtain a documented applicability determination for this DCPMI tier.",
                ),
            )
        allowed = tier_policy.get("applicable", [])
        if allowed and dcpmi_tier not in allowed:
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale=f"This control is scoped to DCPMI tier(s): {', '.join(allowed)}.",
            )

    allowed_roles = rules.get("processing_roles")
    if allowed_roles:
        if processing_role == "Unsure":
            return _review_result(
                framework_id=framework_id,
                control=control,
                rationale="Applicability depends on whether the organisation acts as a controller, processor, or both.",
                recommendation="Confirm the organisation's processing role for the relevant processing activity.",
            )
        if processing_role not in allowed_roles:
            return _not_applicable_result(
                framework_id=framework_id,
                control=control,
                rationale=f"This control is scoped to processing role(s): {', '.join(allowed_roles)}.",
            )

    return None
