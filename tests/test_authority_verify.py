from src.authority_verify import verify_extracted_authority_text


def test_dmb_authority_text_structural_verifier_accepts_expected_landmarks():
    text = """
    Risk-Based Cybersecurity Framework and Guidelines for Deposit Money Banks and Payment Service Banks
    Cybersecurity Self-Assessment. Cyber-Threat Intelligence. Emerging Technologies.
    Security Incident Reporting Template. Artificial Intelligence and Machine Learning.
    """
    result = verify_extracted_authority_text("cbn-dmb-psb-2024", text, page_count=40)
    assert result["passed"] is True
    assert result["missing_markers"] == []
    assert "passing structural check" in result["warning"]


def test_authority_text_structural_verifier_rejects_wrong_document():
    result = verify_extracted_authority_text("cbn-dmb-psb-2024", "unrelated policy", page_count=100)
    assert result["passed"] is False
    assert result["title_match"] is False
    assert result["missing_markers"]
    assert result["warning"].startswith("Structural verification failed")
    assert "do not upgrade" in result["warning"]


def test_manual_visual_verifier_accepts_expected_ofi_landmarks():
    from src.authority_verify import verify_manual_visual_observations

    observed = """
    Risk-Based Cybersecurity Framework and Guidelines for Other Financial Institutions
    Cybersecurity Risk Management System
    Cyber-Threat Intelligence
    Metrics, Monitoring & Reporting
    January 1, 2023
    """
    result = verify_manual_visual_observations("cbn-ofi-2022", observed_text=observed, page_count=43)
    assert result["passed"] is True
    assert result["verification_mode"] == "manual_visual_render_review"
    assert result["manual_visual_verification_required"] is False
