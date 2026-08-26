from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .models import Control, EvidenceMatch, EvidenceType, FreshnessStatus


CURRENT_DAYS = 365
AGING_DAYS = 730

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_DATE_LABEL = re.compile(
    r"(?i)\b(approved|effective|issued|last\s+reviewed|reviewed|document\s+date|date)\s*[:\-]?\s*"
    r"(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(20\d{2})\b"
)
_DATE_LABEL_MONTH_FIRST = re.compile(
    r"(?i)\b(approved|effective|issued|last\s+reviewed|reviewed|document\s+date|date)\s*[:\-]?\s*"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2}),?\s+(20\d{2})\b"
)
_DATE_LABEL_ISO = re.compile(
    r"(?i)\b(approved|effective|issued|last\s+reviewed|reviewed|document\s+date|date)\s*[:\-]?\s*"
    r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"
)


@dataclass(frozen=True)
class EvidenceQuality:
    evidence_type: EvidenceType
    evidence_type_reason: str
    document_date: str | None
    date_source: str | None
    age_days: int | None
    freshness_status: FreshnessStatus
    quality_flags: list[str]


def _normalized_probe(source_name: str, text: str) -> str:
    stem = Path(source_name).stem.replace("_", " ").replace("-", " ")
    return f"{stem}\n{text[:5000]}".lower()


def classify_evidence_type(source_name: str, text: str) -> tuple[EvidenceType, str]:
    probe = _normalized_probe(source_name, text)
    stem = Path(source_name).stem.lower()
    header = text[:500].lower()

    # Document identity wins over incidental words inside the document. A policy that
    # mentions logs/registers is still a policy, not operational proof that those
    # logs/registers exist. Stronger artefact types are checked first below.
    documented_intent_identity = any(
        token in stem or token in header
        for token in ("policy", "procedure", "standard", "runbook", "playbook", "guideline")
    )
    if documented_intent_identity:
        return EvidenceType.DOCUMENTED_INTENT, "policy, procedure, standard or runbook identity detected"

    rules: list[tuple[EvidenceType, tuple[str, ...], str]] = [
        (
            EvidenceType.REGULATORY_FILING,
            (
                "filing acknowledgement",
                "filing acknowledgment",
                "submission receipt",
                "regulatory return",
                "registration certificate",
                "certificate of registration",
                "compliance audit return",
                "regulator submission",
            ),
            "regulatory filing/certificate language detected",
        ),
        (
            EvidenceType.AUDIT_TEST_EVIDENCE,
            (
                "audit report",
                "audit finding",
                "penetration test",
                "pentest",
                "vulnerability assessment",
                "vulnerability scan",
                "tabletop exercise",
                "test result",
                "test evidence",
                "assessment report",
                "internal audit",
            ),
            "audit, assessment, exercise or testing language detected",
        ),
        (
            EvidenceType.TECHNICAL_EVIDENCE,
            (
                "configuration export",
                "configuration backup",
                "firewall rule",
                "security configuration",
                "system configuration",
                "technical configuration",
                "console screenshot",
                "dashboard screenshot",
                "siem alert",
                "edr alert",
                "access control list",
            ),
            "technical configuration or system-output language detected",
        ),
        (
            EvidenceType.TRAINING_EVIDENCE,
            (
                "training attendance",
                "attendance register",
                "training completion",
                "awareness completion",
                "training record",
                "training certificate",
            ),
            "training completion/attendance evidence detected",
        ),
        (
            EvidenceType.CONTRACTUAL_EVIDENCE,
            (
                "data processing agreement",
                "processor agreement",
                "supplier agreement",
                "vendor agreement",
                "service level agreement",
                "contractual clause",
                "contract",
            ),
            "contractual evidence language detected",
        ),
        (
            EvidenceType.OPERATIONAL_RECORD,
            (
                "incident register",
                "risk register",
                "access review report",
                "approval record",
                "remediation ticket",
                "change ticket",
                "meeting minutes",
                "board minutes",
                "event log",
                "audit log",
                "activity log",
                "review record",
                "evidence register",
                "records of",
            ),
            "operational record/log/register language detected",
        ),
        (
            EvidenceType.DOCUMENTED_INTENT,
            (
                " policy ",
                "policy -",
                "policy\n",
                " procedure ",
                "procedure -",
                "procedure\n",
                " standard ",
                "standard -",
                "standard\n",
                " runbook ",
                " guideline ",
            ),
            "policy, procedure, standard or runbook language detected",
        ),
    ]

    padded = f" {probe} "
    for evidence_type, keywords, reason in rules:
        if any(keyword in padded for keyword in keywords):
            return evidence_type, reason

    # Filename-only fallbacks are intentionally conservative.
    if documented_intent_identity:
        return EvidenceType.DOCUMENTED_INTENT, "document-intent filename/header detected"
    if any(token in stem for token in ("audit", "pentest", "assessment", "test_result", "scan")):
        return EvidenceType.AUDIT_TEST_EVIDENCE, "audit/test filename detected"
    if any(token in stem for token in ("register", "log", "ticket", "minutes", "record")):
        return EvidenceType.OPERATIONAL_RECORD, "operational-record filename detected"

    return EvidenceType.UNKNOWN, "no deterministic evidence-type rule matched"


def extract_labeled_document_date(text: str) -> tuple[date | None, str | None]:
    sample = text[:10000]

    match = _DATE_LABEL.search(sample)
    if match:
        label, day, month_name, year = match.groups()
        try:
            return date(int(year), _MONTHS[month_name.lower()], int(day)), f"content:{label.lower().replace(' ', '_')}"
        except ValueError:
            return None, None

    match = _DATE_LABEL_MONTH_FIRST.search(sample)
    if match:
        label, month_name, day, year = match.groups()
        try:
            return date(int(year), _MONTHS[month_name.lower()], int(day)), f"content:{label.lower().replace(' ', '_')}"
        except ValueError:
            return None, None

    match = _DATE_LABEL_ISO.search(sample)
    if match:
        label, year, month, day = match.groups()
        try:
            return date(int(year), int(month), int(day)), f"content:{label.lower().replace(' ', '_')}"
        except ValueError:
            return None, None

    return None, None


def freshness_for_date(document_date: date | None, *, as_of_date: date | None = None) -> tuple[int | None, FreshnessStatus, list[str]]:
    if document_date is None:
        return None, FreshnessStatus.UNKNOWN, ["undated_evidence"]

    as_of_date = as_of_date or date.today()
    age_days = (as_of_date - document_date).days
    if age_days < 0:
        return age_days, FreshnessStatus.UNKNOWN, ["future_document_date"]
    if age_days <= CURRENT_DAYS:
        return age_days, FreshnessStatus.CURRENT, []
    if age_days <= AGING_DAYS:
        return age_days, FreshnessStatus.AGING, ["aging_evidence"]
    return age_days, FreshnessStatus.STALE, ["stale_evidence"]


def build_evidence_quality(
    source_name: str,
    text: str,
    *,
    metadata_date: datetime | date | None = None,
    metadata_date_source: str | None = None,
    as_of_date: date | None = None,
) -> EvidenceQuality:
    evidence_type, type_reason = classify_evidence_type(source_name, text)
    content_date, content_date_source = extract_labeled_document_date(text)

    doc_date = content_date
    date_source = content_date_source
    if doc_date is None and metadata_date is not None:
        doc_date = metadata_date.date() if isinstance(metadata_date, datetime) else metadata_date
        date_source = metadata_date_source or "document_metadata"

    age_days, freshness_status, flags = freshness_for_date(doc_date, as_of_date=as_of_date)
    if evidence_type == EvidenceType.DOCUMENTED_INTENT:
        flags = [*flags, "documented_intent"]

    return EvidenceQuality(
        evidence_type=evidence_type,
        evidence_type_reason=type_reason,
        document_date=doc_date.isoformat() if doc_date else None,
        date_source=date_source,
        age_days=age_days,
        freshness_status=freshness_status,
        quality_flags=flags,
    )


def control_requires_operational_evidence(control: Control) -> bool:
    """Conservatively identify controls whose examples expect proof beyond intent documents."""
    examples = " ".join(control.evidence_examples).lower()
    summary = control.requirement_summary.lower()

    strong_operational_tokens = (
        "log",
        "register",
        "ticket",
        "minutes",
        "report",
        "record",
        "scan",
        "test result",
        "test evidence",
        "exercise",
        "submission",
        "receipt",
        "certificate",
        "configuration",
        "screenshot",
        "metric",
        "audit evidence",
        "attendance",
        "review evidence",
        "assessment result",
    )
    if any(token in examples for token in strong_operational_tokens):
        return True

    action_tokens = (
        "conduct ",
        "perform ",
        "monitor ",
        "submit ",
        "report ",
        "test ",
        "reviewed quarterly",
        "reviewed annually",
        "maintain a register",
        "maintain an inventory",
        "retain evidence",
        "track ",
        "record ",
    )
    return any(token in summary for token in action_tokens)


def assessment_quality_guardrails(control: Control, matches: list[EvidenceMatch], proposed_status: str) -> tuple[str, list[str], str | None]:
    """Apply deterministic caps to strong automated conclusions when evidence quality cannot support them."""
    if proposed_status != "supported" or not matches:
        return proposed_status, [], None

    flags: list[str] = []
    notes: list[str] = []

    if all(match.freshness_status == FreshnessStatus.STALE for match in matches):
        flags.append("stale_only_support")
        notes.append("All retrieved evidence is stale under the general BGNexa age heuristic, so it cannot by itself establish current implementation.")

    if control_requires_operational_evidence(control) and all(
        match.evidence_type == EvidenceType.DOCUMENTED_INTENT for match in matches
    ):
        flags.append("intent_only_for_operational_requirement")
        notes.append("Only policy/procedure intent was retrieved for a requirement that expects operational evidence.")

    if flags:
        return "partially_supported", flags, " ".join(notes)
    return proposed_status, [], None


def evidence_quality_summary(matches: list[EvidenceMatch]) -> str:
    if not matches:
        return "No evidence candidates."
    types = sorted({m.evidence_type.value for m in matches})
    freshness = sorted({m.freshness_status.value for m in matches})
    return f"Evidence types: {', '.join(types)}. Freshness: {', '.join(freshness)}."
