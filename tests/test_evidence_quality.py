from datetime import date

from src.evidence import parse_bytes
from src.evidence_quality import build_evidence_quality
from src.models import EvidenceType, FreshnessStatus


def test_policy_identity_is_not_misclassified_as_operational_record():
    text = b"Access Control Policy - Approved 15 January 2026. The manager retains quarterly access review reports and remediation tickets."
    chunks = parse_bytes("access_control_policy.txt", text, as_of_date=date(2026, 8, 26))
    assert chunks
    assert chunks[0].evidence_type == EvidenceType.DOCUMENTED_INTENT
    assert chunks[0].document_date == "2026-01-15"
    assert chunks[0].freshness_status == FreshnessStatus.CURRENT
    assert "documented_intent" in chunks[0].quality_flags


def test_stale_audit_evidence_is_flagged():
    quality = build_evidence_quality(
        "penetration_test_report.txt",
        "Penetration Test Report - Issued 01 January 2023. Findings were recorded.",
        as_of_date=date(2026, 8, 26),
    )
    assert quality.evidence_type == EvidenceType.AUDIT_TEST_EVIDENCE
    assert quality.freshness_status == FreshnessStatus.STALE
    assert "stale_evidence" in quality.quality_flags


def test_undated_evidence_keeps_unknown_freshness():
    quality = build_evidence_quality(
        "firewall_export.txt",
        "Configuration export showing firewall rules and enabled logging.",
        as_of_date=date(2026, 8, 26),
    )
    assert quality.evidence_type == EvidenceType.TECHNICAL_EVIDENCE
    assert quality.document_date is None
    assert quality.freshness_status == FreshnessStatus.UNKNOWN
    assert "undated_evidence" in quality.quality_flags


def test_future_document_date_is_not_treated_as_current():
    quality = build_evidence_quality(
        "policy.txt",
        "Security Policy - Approved 01 January 2027.",
        as_of_date=date(2026, 8, 26),
    )
    assert quality.freshness_status == FreshnessStatus.UNKNOWN
    assert "future_document_date" in quality.quality_flags


def test_documented_standard_identity_wins_over_filing_words_inside_content():
    quality = build_evidence_quality(
        "privacy_governance.txt",
        "Privacy Governance Standard - Approved 18 March 2026. Known gap: no registration certificate or filing acknowledgement is available.",
        as_of_date=date(2026, 8, 26),
    )
    assert quality.evidence_type == EvidenceType.DOCUMENTED_INTENT
