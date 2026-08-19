from pathlib import Path

from src.framework_loader import load_frameworks
from src.provenance import audit_framework_provenance, provenance_summary, verification_tier


ROOT = Path(__file__).resolve().parents[1]


def test_framework_provenance_has_no_errors_after_direct_dmb_verification():
    frameworks = load_frameworks(ROOT / "frameworks")
    summary = provenance_summary(frameworks)

    assert summary["frameworks"] == 7
    assert summary["controls"] >= 210
    assert summary["errors"] == 0
    assert summary["warnings"] == 0


def test_known_verification_statuses_map_to_explicit_tiers():
    assert verification_tier("official_text_cross_checked") == "authority_traceable"
    assert verification_tier("official_reference_paraphrase") == "authority_traceable"
    assert verification_tier("direct_authority_pdf_verified") == "authority_traceable"
    assert verification_tier("authority_document_cross_checked_via_archival_full_text") == "authority_metadata_plus_archival_text"
    assert verification_tier("official_metadata_plus_archival_text_pending_direct") == "authority_metadata_plus_secondary_text_pending_direct"


def test_expanded_ndpa_and_gaid_seed_controls_are_present():
    frameworks = load_frameworks(ROOT / "frameworks")
    ndpa = frameworks["ndpa-2023"]
    gaid = frameworks["ndpc-gaid-2025"]

    ndpa_ids = {control.control_id for control in ndpa.controls}
    gaid_ids = {control.control_id for control in gaid.controls}

    assert {
        "NDPA-25",
        "NDPA-26",
        "NDPA-27",
        "NDPA-28",
        "NDPA-29",
        "NDPA-30",
        "NDPA-31",
        "NDPA-32",
        "NDPA-34",
        "NDPA-35",
        "NDPA-36",
        "NDPA-37",
        "NDPA-38",
        "NDPA-39",
        "NDPA-40",
        "NDPA-41",
        "NDPA-44",
    }.issubset(ndpa_ids)
    assert {
        "GAID-07",
        "GAID-08",
        "GAID-09",
        "GAID-10",
        "GAID-11",
        "GAID-12",
        "GAID-DPO-REPORT",
        "GAID-29",
        "GAID-30",
        "GAID-33",
        "GAID-34",
    }.issubset(gaid_ids)

    ndpa_locators = {control.control_id: control.source_locator for control in ndpa.controls}
    assert "Sections 41-43" in ndpa_locators["NDPA-41"]

    locators = {control.control_id: control.source_locator for control in gaid.controls}
    assert "Article 29" in locators["GAID-29"]
    assert "Article 30" in locators["GAID-30"]
    assert "Article 33" in locators["GAID-33"]
    assert "Article 34" in locators["GAID-34"]


def test_cbn_dmb_psb_verified_pack_has_expanded_30_control_surface():
    frameworks = load_frameworks(ROOT / "frameworks")
    dmb = frameworks["cbn-dmb-psb-2024"]
    ids = {control.control_id for control in dmb.controls}

    assert len(dmb.controls) == 30
    assert {
        "CBN-DMBPSB-1.3-1.4",
        "CBN-DMBPSB-2.1.4",
        "CBN-DMBPSB-3.5",
        "CBN-DMBPSB-3.6",
        "CBN-DMBPSB-APP3-1.1",
        "CBN-DMBPSB-APP3-1.2",
        "CBN-DMBPSB-APP3-1.8",
        "CBN-DMBPSB-APP3-2.1",
        "CBN-DMBPSB-APP3-3",
        "CBN-DMBPSB-APP4-AI",
    }.issubset(ids)
    assert all(control.verification_status == "direct_authority_pdf_verified" for control in dmb.controls)
    assert all(control.source_pdf_pages for control in dmb.controls)


def test_ofi_pack_is_directly_verified_from_scanned_authority_source():
    frameworks = load_frameworks(ROOT / "frameworks")
    ofi = frameworks["cbn-ofi-2022"]
    assert len(ofi.controls) == 21
    assert all(control.verification_status == "direct_authority_pdf_verified" for control in ofi.controls)
    assert all(control.source_pdf_pages for control in ofi.controls)


def test_nist_and_gdpr_stage4_packs_have_expected_surfaces():
    frameworks = load_frameworks(ROOT / "frameworks")
    nist = frameworks["nist-csf-2.0"]
    gdpr = frameworks["gdpr-2016-679"]
    assert nist.framework_type == "voluntary_framework"
    assert len(nist.controls) == 106
    assert nist.controls[0].reference == "GV.OC-01"
    assert nist.controls[-1].reference == "RC.CO-04"
    assert gdpr.framework_type == "law"
    assert len(gdpr.controls) == 18
    assert all(control.applicability.get("requires_gdpr_scope") for control in gdpr.controls)
