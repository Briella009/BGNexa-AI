from __future__ import annotations

import hashlib
from datetime import date

from src.evidence import parse_bytes_with_source_record
from src.evidence_quality import build_evidence_quality
from src.models import (
    AssessmentResult,
    AssessmentStatus,
    Control,
    EvidenceMatch,
    EvidenceType,
    Framework,
    FrameworkSource,
    FreshnessStatus,
)
from src.report import evidence_quality_dataframe
from src.retriever import EvidenceRetriever
from src.review import build_assessment_snapshot, verify_snapshot_digest
from src.scoring import calculate_score


AS_OF = date(2026, 8, 26)


def _framework() -> Framework:
    source = FrameworkSource(
        authority="Test Authority",
        title="Test Framework",
        version="1",
        source_url="https://example.test/framework",
        last_verified="2026-08-26",
    )
    control = Control(
        control_id="C1",
        reference="1",
        title="Risk management",
        requirement_summary="Maintain and review information-security risks and treatment actions.",
        evidence_examples=["risk register", "risk treatment records"],
        source_locator="1",
        verification_status="verified",
    )
    return Framework(
        framework_id="fw",
        name="Test Framework",
        jurisdiction="Test",
        version="1",
        authority="Test Authority",
        source=source,
        scope_note="test",
        controls=[control],
    )


def test_filename_date_fallback_makes_undated_txt_traceably_current():
    quality = build_evidence_quality(
        "2026-02-22_Privacy_and_Data_Protection_Policy.txt",
        "Privacy and Data Protection Policy\nOwner: Data Protection Lead",
        as_of_date=AS_OF,
    )
    assert quality.document_date == "2026-02-22"
    assert quality.date_source == "filename:date"
    assert quality.freshness_status == FreshnessStatus.CURRENT
    assert "filename_date_inferred" in quality.quality_flags


def test_explicit_operational_risk_register_is_not_flattened_to_policy_intent():
    quality = build_evidence_quality(
        "2026-06-30_Information_Security_Risk_Assessment.txt",
        """Record type: Operational record - Information Security Risk Assessment Register
Assessment date: 30 June 2026
RISK-001 | Privileged account compromise
Owner: Infrastructure Manager
Status: In progress
Treatment: Implement just-in-time privileged elevation
""",
        as_of_date=AS_OF,
    )
    assert quality.evidence_type == EvidenceType.OPERATIONAL_RECORD
    assert EvidenceType.OPERATIONAL_RECORD in quality.evidence_type_tags
    assert quality.document_date == "2026-06-30"
    assert quality.freshness_status == FreshnessStatus.CURRENT


def test_training_and_internal_audit_record_keeps_composite_evidence_tags_without_false_filing():
    quality = build_evidence_quality(
        "2026-07-18_Security_Training_and_Internal_Audit_Evidence.md",
        """# Security Training and Internal Audit Evidence
**Record type:** Operational record
**Record date:** 18 July 2026
Training completion rate: 98.9%
## Internal control review
### Test results
Two exceptions remain open in the assurance action register.
## Deliberate test limitation
This pack does not include regulator registration certificates or statutory returns.
""",
        as_of_date=AS_OF,
    )
    assert quality.evidence_type == EvidenceType.OPERATIONAL_RECORD
    assert EvidenceType.TRAINING_EVIDENCE in quality.evidence_type_tags
    assert EvidenceType.AUDIT_TEST_EVIDENCE in quality.evidence_type_tags
    assert EvidenceType.REGULATORY_FILING not in quality.evidence_type_tags
    assert quality.document_date == "2026-07-18"
    assert quality.date_source == "content:record_date"


def test_source_record_preserves_full_file_sha256_and_never_depends_on_retrieval():
    content = b"2026 risk register. Record type: Operational record. Status: Open. Owner: Security."
    chunks, record = parse_bytes_with_source_record(
        "2026-06-30_risk_register.txt",
        content,
        as_of_date=AS_OF,
    )
    assert chunks
    expected_hash = hashlib.sha256(content).hexdigest()
    assert record.source_hash == expected_hash
    assert record.parse_status == "parsed"
    assert record.chunk_count == len(chunks)
    assert all(chunk.source_hash == expected_hash for chunk in chunks)


def test_parse_failure_is_registered_instead_of_silently_disappearing():
    content = b"opaque-binary-content"
    chunks, record = parse_bytes_with_source_record("unsupported.bin", content, as_of_date=AS_OF)
    assert chunks == []
    assert record.parse_status == "parse_error"
    assert record.source_hash == hashlib.sha256(content).hexdigest()
    assert record.parse_error
    assert "parse_error" in record.quality_flags


def test_retriever_preserves_document_provenance_on_matches():
    content = b"Record type: Operational record. Risk register with treatment owner and open remediation actions."
    chunks, record = parse_bytes_with_source_record("2026-06-30_risk_register.txt", content, as_of_date=AS_OF)
    control = _framework().controls[0]
    matches = EvidenceRetriever(chunks, min_score=0.0).retrieve(control, top_k=1)
    assert matches
    assert matches[0].source_hash == record.source_hash
    assert matches[0].source_size_bytes == len(content)
    assert EvidenceType.OPERATIONAL_RECORD in matches[0].evidence_type_tags


def test_source_register_keeps_indexed_but_not_retrieved_documents_visible():
    risk_chunks, risk_record = parse_bytes_with_source_record(
        "2026-06-30_risk_register.txt",
        b"Record type: Operational record. Risk register with treatment actions.",
        as_of_date=AS_OF,
    )
    _, policy_record = parse_bytes_with_source_record(
        "2026-03-15_access_policy.txt",
        b"Access Control Policy. Role based access and MFA are required.",
        as_of_date=AS_OF,
    )

    fw = _framework()
    first = risk_chunks[0]
    match = EvidenceMatch(
        chunk_id=first.chunk_id,
        source_name=first.source_name,
        excerpt=first.text,
        retrieval_score=0.9,
        content_hash=first.content_hash,
        source_hash=first.source_hash,
        source_size_bytes=first.source_size_bytes,
        source_extension=first.source_extension,
        evidence_type=first.evidence_type,
        evidence_type_tags=first.evidence_type_tags,
        document_date=first.document_date,
        date_source=first.date_source,
        age_days=first.age_days,
        freshness_status=first.freshness_status,
        quality_flags=first.quality_flags,
    )
    result = AssessmentResult(
        control_id="C1",
        framework_id="fw",
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale="review",
        evidence=[match],
    )
    bundle = {"fw": {"framework": fw, "results": [result], "score": calculate_score(fw.controls, [result])}}

    df = evidence_quality_dataframe(bundle, source_records=[risk_record, policy_record])
    assert len(df) == 2
    usage = dict(zip(df["source"], df["assessment_use"]))
    assert usage["2026-06-30_risk_register.txt"] == "retrieved"
    assert usage["2026-03-15_access_policy.txt"] == "indexed_not_retrieved"


def test_snapshot_contains_document_level_provenance_for_all_supplied_sources():
    chunks, record = parse_bytes_with_source_record(
        "2026-06-30_risk_register.txt",
        b"Record type: Operational record. Risk register with treatment actions.",
        as_of_date=AS_OF,
    )
    fw = _framework()
    result = AssessmentResult(
        control_id="C1",
        framework_id="fw",
        status=AssessmentStatus.REVIEW_REQUIRED,
        rationale="review",
        evidence=[],
    )
    bundle = {"fw": {"framework": fw, "results": [result], "score": calculate_score(fw.controls, [result])}}
    snapshot = build_assessment_snapshot(
        bundle,
        organisation_profile={"organisation_name": "Example"},
        source_records=[record],
        created_at="2026-08-26T00:00:00+00:00",
    )
    assert snapshot["snapshot_schema"] == "readiness-copilot/v3"
    assert snapshot["evidence_sources"][0]["source_hash"] == record.source_hash
    assert snapshot["evidence_sources"][0]["source_name"] == record.source_name
    assert verify_snapshot_digest(snapshot)
