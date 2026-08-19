from pathlib import Path

from src.framework_loader import load_frameworks


ROOT = Path(__file__).resolve().parents[1]


def test_expected_frameworks_load():
    frameworks = load_frameworks(ROOT / "frameworks")
    assert {
        "ndpa-2023",
        "ndpc-gaid-2025",
        "cbn-ofi-2022",
        "cbn-dmb-psb-2024",
        "iso-iec-27001-2022-amd1-2024",
        "nist-csf-2.0",
        "gdpr-2016-679",
    }.issubset(frameworks)


def test_every_control_is_traceable():
    frameworks = load_frameworks(ROOT / "frameworks")
    for framework in frameworks.values():
        assert framework.source.source_url.startswith("https://")
        assert framework.source.last_verified
        for control in framework.controls:
            assert control.reference
            assert control.source_locator
            assert control.verification_status
            assert control.requirement_summary


def test_iso_public_pack_does_not_claim_to_include_standard_text():
    frameworks = load_frameworks(ROOT / "frameworks")
    iso = frameworks["iso-iec-27001-2022-amd1-2024"]
    assert iso.copyright_mode == "reference_only_no_standard_text"
    assert all(control.verification_status == "official_reference_paraphrase" for control in iso.controls)
    assert all("annex a" not in control.requirement_summary.lower() for control in iso.controls)


def test_dmb_psb_controls_are_direct_pdf_verified_with_page_refs():
    frameworks = load_frameworks(ROOT / "frameworks")
    fw = frameworks["cbn-dmb-psb-2024"]
    assert fw.controls
    assert all(c.verification_status == "direct_authority_pdf_verified" for c in fw.controls)
    assert all(c.source_pdf_pages for c in fw.controls)


def test_nist_pack_contains_complete_csf_2_core_subcategory_surface():
    frameworks = load_frameworks(ROOT / "frameworks")
    nist = frameworks["nist-csf-2.0"]
    assert len(nist.controls) == 106
    assert {"GV.OC-01", "ID.AM-01", "PR.AA-01", "DE.CM-01", "RS.MA-01", "RC.CO-04"}.issubset(
        {control.reference for control in nist.controls}
    )


def test_cbn_ofi_controls_are_direct_visual_authority_verified_with_page_refs():
    frameworks = load_frameworks(ROOT / "frameworks")
    fw = frameworks["cbn-ofi-2022"]
    assert len(fw.controls) == 21
    assert all(c.verification_status == "direct_authority_pdf_verified" for c in fw.controls)
    assert all(c.source_pdf_pages for c in fw.controls)
