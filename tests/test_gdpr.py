from pathlib import Path

from src.applicability import recommended_framework_ids, resolve_control_applicability
from src.framework_loader import load_frameworks
from src.gdpr import triage_gdpr_article3
from src.models import AssessmentStatus


ROOT = Path(__file__).resolve().parents[1]


def test_article3_triage_flags_eu_establishment():
    result = triage_gdpr_article3(
        eu_establishment="Yes",
        offers_goods_services_to_people_in_eu="No",
        monitors_behaviour_in_eu="No",
        member_state_law_by_public_international_law="No",
    )
    assert result.candidate_status == "candidate_in_scope"
    assert any("3(1)" in item for item in result.basis)


def test_article3_triage_flags_goods_services_or_monitoring():
    goods = triage_gdpr_article3(
        eu_establishment="No",
        offers_goods_services_to_people_in_eu="Yes",
        monitors_behaviour_in_eu="No",
        member_state_law_by_public_international_law="No",
    )
    monitor = triage_gdpr_article3(
        eu_establishment="No",
        offers_goods_services_to_people_in_eu="No",
        monitors_behaviour_in_eu="Yes",
        member_state_law_by_public_international_law="No",
    )
    assert goods.candidate_status == "candidate_in_scope"
    assert monitor.candidate_status == "candidate_in_scope"


def test_article3_triage_all_no_is_not_a_legal_determination():
    result = triage_gdpr_article3(
        eu_establishment="No",
        offers_goods_services_to_people_in_eu="No",
        monitors_behaviour_in_eu="No",
        member_state_law_by_public_international_law="No",
    )
    assert result.candidate_status == "no_article3_trigger_identified"
    assert any("qualified reviewer" in item for item in result.caveats)


def test_article3_triage_unknown_remains_unresolved():
    result = triage_gdpr_article3(
        eu_establishment="Unknown",
        offers_goods_services_to_people_in_eu="No",
        monitors_behaviour_in_eu="No",
        member_state_law_by_public_international_law="No",
    )
    assert result.candidate_status == "insufficient_information"


def test_gdpr_unknown_scope_never_becomes_evidence_assessable():
    fw = load_frameworks(ROOT / "frameworks")["gdpr-2016-679"]
    control = next(c for c in fw.controls if c.control_id == "GDPR-32")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Controller",
        gdpr_scope_status="Unknown",
    )
    assert result is not None
    assert result.status == AssessmentStatus.REVIEW_REQUIRED


def test_gdpr_confirmed_out_of_scope_is_not_applicable():
    fw = load_frameworks(ROOT / "frameworks")["gdpr-2016-679"]
    control = next(c for c in fw.controls if c.control_id == "GDPR-32")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Controller",
        gdpr_scope_status="No",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_gdpr_role_is_resolved_before_controller_specific_conditions():
    fw = load_frameworks(ROOT / "frameworks")["gdpr-2016-679"]
    control = next(c for c in fw.controls if c.control_id == "GDPR-28-C")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Processor",
        gdpr_scope_status="Yes",
        gdpr_uses_processors_status="Unknown",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_gdpr_conditional_dpo_unknown_requires_review():
    fw = load_frameworks(ROOT / "frameworks")["gdpr-2016-679"]
    control = next(c for c in fw.controls if c.control_id == "GDPR-37")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Controller",
        gdpr_scope_status="Yes",
        gdpr_dpo_required_status="Unknown",
    )
    assert result is not None
    assert result.status == AssessmentStatus.REVIEW_REQUIRED


def test_gdpr_conditional_dpo_no_is_not_applicable():
    fw = load_frameworks(ROOT / "frameworks")["gdpr-2016-679"]
    control = next(c for c in fw.controls if c.control_id == "GDPR-37")
    result = resolve_control_applicability(
        framework_id=fw.framework_id,
        control=control,
        dcpmi_status="No",
        processing_role="Controller",
        gdpr_scope_status="Yes",
        gdpr_dpo_required_status="No",
    )
    assert result is not None
    assert result.status == AssessmentStatus.NOT_APPLICABLE


def test_recommendations_can_add_nist_and_gdpr_without_changing_nigeria_defaults():
    ids = recommended_framework_ids(
        operates_in_nigeria=True,
        cbn_regulated_type="Not CBN-regulated / Unknown",
        include_iso=True,
        include_nist=True,
        include_gdpr=True,
    )
    assert {"ndpa-2023", "ndpc-gaid-2025", "iso-iec-27001-2022-amd1-2024", "nist-csf-2.0", "gdpr-2016-679"}.issubset(ids)
