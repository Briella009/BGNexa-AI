import pytest

from src.dcpmi import triage_dcpmi


def test_schedule7_specific_fintech_maps_to_uhl_candidate():
    result = triage_dcpmi(organisation_type="Fintech")
    assert result.candidate_status == "candidate_dcpmi"
    assert result.candidate_tier == "UHL"
    assert result.requires_human_confirmation is True


def test_schedule7_microfinance_bank_maps_to_ehl_candidate():
    result = triage_dcpmi(organisation_type="Microfinance bank")
    assert result.candidate_tier == "EHL"


def test_volume_over_5000_maps_to_uhl():
    result = triage_dcpmi(data_subjects_six_months=5001)
    assert result.candidate_status == "candidate_dcpmi"
    assert result.candidate_tier == "UHL"


def test_exact_numeric_boundaries_are_not_silently_assigned_to_tier():
    for count in (1000, 5000):
        result = triage_dcpmi(data_subjects_six_months=count)
        assert result.candidate_status == "candidate_dcpmi"
        assert result.candidate_tier == "unknown"
        assert result.ambiguities


def test_sensitive_data_processor_over_200_maps_to_ohl():
    result = triage_dcpmi(
        sensitive_personal_data_commercial_subjects=201,
        processing_role="Processor",
    )
    assert result.candidate_status == "candidate_dcpmi"
    assert result.candidate_tier == "OHL"


def test_broad_sector_is_dcpmi_indicator_but_not_tier_decision():
    result = triage_dcpmi(sector="Financial")
    assert result.candidate_status == "candidate_dcpmi"
    assert result.candidate_tier == "unknown"
    assert result.ambiguities


def test_no_trigger_is_not_presented_as_legal_no():
    result = triage_dcpmi(data_subjects_six_months=150, sector="Other")
    assert result.candidate_status == "no_trigger_identified"
    assert result.candidate_tier == "unknown"
    assert "not a legal finding" in " ".join(result.ambiguities).lower()


def test_negative_volume_is_rejected():
    with pytest.raises(ValueError):
        triage_dcpmi(data_subjects_six_months=-1)
