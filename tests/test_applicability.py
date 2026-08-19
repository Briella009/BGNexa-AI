from pathlib import Path

from src.applicability import recommended_framework_ids, resolve_control_applicability
from src.framework_loader import load_frameworks
from src.models import AssessmentStatus


ROOT = Path(__file__).resolve().parents[1]


def test_cbn_frameworks_are_selected_separately():
    ofi = recommended_framework_ids(operates_in_nigeria=True, cbn_regulated_type="OFI", include_iso=False)
    dmb = recommended_framework_ids(operates_in_nigeria=True, cbn_regulated_type="DMB/PSB", include_iso=False)
    assert "cbn-ofi-2022" in ofi
    assert "cbn-dmb-psb-2024" not in ofi
    assert "cbn-dmb-psb-2024" in dmb
    assert "cbn-ofi-2022" not in dmb


def test_unknown_dcpmi_never_becomes_not_applicable_or_supported():
    fw = load_frameworks(ROOT / "frameworks")["ndpa-2023"]
    control = next(c for c in fw.controls if c.control_id == "NDPA-44")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Unknown",
        processing_role="Both",
    )
    assert result is not None
    assert result.status == AssessmentStatus.REVIEW_REQUIRED


def test_known_non_dcpmi_is_not_applicable_for_dcpmi_scoped_control():
    fw = load_frameworks(ROOT / "frameworks")["ndpa-2023"]
    control = next(c for c in fw.controls if c.control_id == "NDPA-44")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Both",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_controller_specific_dpo_control_not_applied_to_processor_only_profile():
    fw = load_frameworks(ROOT / "frameworks")["ndpa-2023"]
    control = next(c for c in fw.controls if c.control_id == "NDPA-32")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Yes",
        processing_role="Processor",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_gaid_car_uhl_is_evidence_assessable_when_dcpmi_confirmed():
    fw = load_frameworks(ROOT / "frameworks")["ndpc-gaid-2025"]
    control = next(c for c in fw.controls if c.control_id == "GAID-10")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Yes",
        dcpmi_tier="UHL",
        registration_exempt_status="No",
        processing_role="Both",
    )
    assert result is None


def test_gaid_car_ohl_is_manual_review_due_to_source_scope_tension():
    fw = load_frameworks(ROOT / "frameworks")["ndpc-gaid-2025"]
    control = next(c for c in fw.controls if c.control_id == "GAID-10")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Yes",
        dcpmi_tier="OHL",
        registration_exempt_status="No",
        processing_role="Controller",
    )
    assert result is not None
    assert result.status == AssessmentStatus.REVIEW_REQUIRED
    assert "Article 7(c)" in result.rationale
    assert "Article 10(6)" in result.rationale


def test_registration_exemption_controller_can_make_registration_control_not_applicable():
    fw = load_frameworks(ROOT / "frameworks")["ndpc-gaid-2025"]
    control = next(c for c in fw.controls if c.control_id == "GAID-09")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Yes",
        dcpmi_tier="EHL",
        registration_exempt_status="Yes",
        processing_role="Controller",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_registration_exemption_not_generalised_to_processor_role():
    fw = load_frameworks(ROOT / "frameworks")["ndpc-gaid-2025"]
    control = next(c for c in fw.controls if c.control_id == "GAID-09")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="Yes",
        dcpmi_tier="EHL",
        registration_exempt_status="Yes",
        processing_role="Processor",
    )
    assert result is not None
    assert result.status == AssessmentStatus.REVIEW_REQUIRED
