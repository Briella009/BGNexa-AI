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

_MONTH_PATTERN = r"January|February|March|April|May|June|July|August|September|October|November|December"

# Priority matters. A document's record/effective/assessment date is usually a more
# defensible freshness anchor than an incidental review date buried later in the file.
_DATE_LABELS: tuple[tuple[str, str], ...] = (
    (r"effective\s*/\s*record\s+date", "effective_record_date"),
    (r"record\s+date", "record_date"),
    (r"effective\s+date", "effective_date"),
    (r"assessment\s+date", "assessment_date"),
    (r"document\s+date", "document_date"),
    (r"issued", "issued"),
    (r"approved", "approved"),
    (r"last\s+reviewed", "last_reviewed"),
    (r"review\s+date", "review_date"),
    (r"reviewed", "reviewed"),
    (r"date", "date"),
)

_FILENAME_DATE = re.compile(r"(?<!\d)(20\d{2})[-_.](\d{1,2})[-_.](\d{1,2})(?!\d)")
_FILENAME_DATE_COMPACT = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")


@dataclass(frozen=True)
class EvidenceQuality:
    evidence_type: EvidenceType
    evidence_type_tags: list[EvidenceType]
    evidence_type_reason: str
    document_date: str | None
    date_source: str | None
    age_days: int | None
    freshness_status: FreshnessStatus
    quality_flags: list[str]


def _normalized_probe(source_name: str, text: str) -> str:
    stem = Path(source_name).stem.replace("_", " ").replace("-", " ")
    return f"{stem}\n{text[:5000]}".lower()


def _positive_evidence_probe(source_name: str, text: str) -> str:
    """Return a conservative probe that excludes explicit limitation sections.

    Beta evidence often contains statements such as "this pack does not include a
    registration certificate". Those negative statements must not make the file
    look like a regulatory filing. We therefore classify using the document name,
    header and positive body, stopping at common limitation headings.
    """

    lower = text.lower()
    cut_points = []
    for marker in (
        "deliberate test limitation",
        "known limitation",
        "limitations",
        "evidence not provided",
        "not included in this pack",
    ):
        pos = lower.find(marker)
        if pos >= 0:
            cut_points.append(pos)
    if cut_points:
        text = text[: min(cut_points)]
    return _normalized_probe(source_name, text)


def _contains_any(probe: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in probe for keyword in keywords)


def classify_evidence_types(source_name: str, text: str) -> tuple[EvidenceType, list[EvidenceType], str]:
    """Classify the primary evidence type and preserve secondary type signals.

    A single artefact can legitimately contain more than one evidence mode (for
    example a training completion record that also contains internal-audit test
    results). The primary type drives conservative guardrails while ``tags`` keep
    those additional signals visible for reviewers and exports.
    """

    probe = _positive_evidence_probe(source_name, text)
    stem = Path(source_name).stem.lower().replace("_", " ").replace("-", " ")
    header = " ".join(re.sub(r"[*_`#]+", "", text[:1200].lower()).split())

    intent_tokens = ("policy", "procedure", "standard", "runbook", "playbook", "guideline")
    filename_intent = any(re.search(rf"\b{re.escape(token)}\b", stem) for token in intent_tokens)
    title_lines = [line.strip().lower() for line in text.splitlines()[:8] if line.strip()]
    header_intent = any(
        any(re.search(rf"\b{re.escape(token)}\b", line) for token in intent_tokens)
        and not any(marker in line for marker in ("audit", "test result", "evidence record", "operational record"))
        for line in title_lines
    )

    explicit_operational = bool(
        re.search(r"\brecord\s+type\s*[:|\-]?\s*operational\s+record\b", header)
        or "operational record -" in header
    )

    signals: list[tuple[EvidenceType, bool, str]] = [
        (
            EvidenceType.REGULATORY_FILING,
            _contains_any(
                probe,
                (
                    "filing acknowledgement",
                    "filing acknowledgment",
                    "submission receipt",
                    "regulatory return submitted",
                    "registration certificate number",
                    "certificate of registration no",
                    "compliance audit return submitted",
                    "regulator submission receipt",
                    "filing reference",
                ),
            )
            or _contains_any(stem, ("filing receipt", "registration certificate", "regulatory return", "submission receipt")),
            "regulatory filing, certificate or submission-receipt evidence detected",
        ),
        (
            EvidenceType.TRAINING_EVIDENCE,
            _contains_any(
                probe,
                (
                    "training attendance",
                    "attendance register",
                    "training completion",
                    "awareness completion",
                    "training record",
                    "training certificate",
                    "completion rate",
                    "assigned workforce population",
                    "security and privacy awareness",
                ),
            )
            or ("training" in stem and _contains_any(probe, ("completed", "attendance", "completion", "learning platform"))),
            "training completion, attendance or awareness record detected",
        ),
        (
            EvidenceType.AUDIT_TEST_EVIDENCE,
            _contains_any(
                probe,
                (
                    "audit report",
                    "audit finding",
                    "internal audit",
                    "internal control review",
                    "penetration test",
                    "pentest",
                    "vulnerability assessment",
                    "vulnerability scan",
                    "tabletop exercise",
                    "test results",
                    "test result",
                    "test evidence",
                    "assessment report",
                    "sample of 25",
                ),
            )
            or _contains_any(stem, ("audit", "pentest", "test result", "vulnerability scan")),
            "audit, assessment, exercise or testing evidence detected",
        ),
        (
            EvidenceType.TECHNICAL_EVIDENCE,
            _contains_any(
                probe,
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
                    "audit trail export",
                ),
            ),
            "technical configuration or system-output evidence detected",
        ),
        (
            EvidenceType.CONTRACTUAL_EVIDENCE,
            _contains_any(
                probe,
                (
                    "data processing agreement",
                    "processor agreement",
                    "supplier agreement",
                    "vendor agreement",
                    "service level agreement",
                    "executed contract",
                    "signed agreement",
                ),
            ),
            "contractual evidence detected",
        ),
        (
            EvidenceType.OPERATIONAL_RECORD,
            explicit_operational
            or _contains_any(
                probe,
                (
                    "incident register",
                    "risk register",
                    "risk assessment register",
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
                    "assurance action register",
                    "status: in progress",
                    "status: open",
                ),
            )
            or _contains_any(stem, ("register", "log", "ticket", "minutes", "record")),
            "operational record, log, register, action or tracked-review evidence detected",
        ),
    ]

    # A document whose identity is explicitly a policy/procedure/standard remains
    # documented intent even if it lists the records that should exist.
    if filename_intent or (header_intent and not explicit_operational):
        return EvidenceType.DOCUMENTED_INTENT, [EvidenceType.DOCUMENTED_INTENT], "document-intent filename identity detected"

    detected = [evidence_type for evidence_type, matched, _ in signals if matched]

    # Explicit record identity is the strongest signal that a document is evidence
    # of an activity rather than merely a statement of intended controls.
    if explicit_operational:
        tags = [EvidenceType.OPERATIONAL_RECORD, *[t for t in detected if t != EvidenceType.OPERATIONAL_RECORD]]
        return EvidenceType.OPERATIONAL_RECORD, tags, "explicit operational-record identity detected"

    # Regulatory filing proof is deliberately strict and takes precedence only when
    # positive submission/certificate language is present, not merely a mention.
    priority = (
        EvidenceType.REGULATORY_FILING,
        EvidenceType.TECHNICAL_EVIDENCE,
        EvidenceType.TRAINING_EVIDENCE,
        EvidenceType.AUDIT_TEST_EVIDENCE,
        EvidenceType.CONTRACTUAL_EVIDENCE,
        EvidenceType.OPERATIONAL_RECORD,
    )
    for candidate in priority:
        if candidate in detected:
            reason = next(reason for evidence_type, matched, reason in signals if evidence_type == candidate and matched)
            return candidate, detected, reason

    # Header/title fallback for intent documents that were not obvious from filename.
    first_lines = " ".join(title_lines)
    if any(re.search(rf"\b{re.escape(token)}\b", first_lines) for token in intent_tokens):
        return EvidenceType.DOCUMENTED_INTENT, [EvidenceType.DOCUMENTED_INTENT], "document-intent title/header detected"

    return EvidenceType.UNKNOWN, [], "no deterministic evidence-type rule matched"


def classify_evidence_type(source_name: str, text: str) -> tuple[EvidenceType, str]:
    """Backward-compatible primary evidence-type classifier."""

    evidence_type, _, reason = classify_evidence_types(source_name, text)
    return evidence_type, reason


def extract_labeled_document_date(text: str) -> tuple[date | None, str | None]:
    sample = re.sub(r"[*_`#]+", "", text[:12000])

    for label_pattern, label_name in _DATE_LABELS:
        separators = r"\s*(?:[:|\-]|\bis\b)?\s*"
        day_first = re.compile(
            rf"(?i)\b(?:{label_pattern})\b{separators}(\d{{1,2}})\s+({_MONTH_PATTERN})\s+(20\d{{2}})\b"
        )
        month_first = re.compile(
            rf"(?i)\b(?:{label_pattern})\b{separators}({_MONTH_PATTERN})\s+(\d{{1,2}}),?\s+(20\d{{2}})\b"
        )
        iso = re.compile(
            rf"(?i)\b(?:{label_pattern})\b{separators}(20\d{{2}})[-/](\d{{1,2}})[-/](\d{{1,2}})\b"
        )

        match = day_first.search(sample)
        if match:
            day, month_name, year = match.groups()
            try:
                return date(int(year), _MONTHS[month_name.lower()], int(day)), f"content:{label_name}"
            except ValueError:
                pass

        match = month_first.search(sample)
        if match:
            month_name, day, year = match.groups()
            try:
                return date(int(year), _MONTHS[month_name.lower()], int(day)), f"content:{label_name}"
            except ValueError:
                pass

        match = iso.search(sample)
        if match:
            year, month, day = match.groups()
            try:
                return date(int(year), int(month), int(day)), f"content:{label_name}"
            except ValueError:
                pass

    return None, None


def extract_filename_document_date(source_name: str) -> tuple[date | None, str | None]:
    """Extract an explicit YYYY-MM-DD style date embedded in the source filename."""

    stem = Path(source_name).stem
    for pattern in (_FILENAME_DATE, _FILENAME_DATE_COMPACT):
        match = pattern.search(stem)
        if not match:
            continue
        year, month, day = match.groups()
        try:
            return date(int(year), int(month), int(day)), "filename:date"
        except ValueError:
            continue
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
    evidence_type, evidence_type_tags, type_reason = classify_evidence_types(source_name, text)
    content_date, content_date_source = extract_labeled_document_date(text)
    filename_date, filename_date_source = extract_filename_document_date(source_name)

    doc_date = content_date
    date_source = content_date_source
    if doc_date is None and filename_date is not None:
        doc_date = filename_date
        date_source = filename_date_source
    if doc_date is None and metadata_date is not None:
        doc_date = metadata_date.date() if isinstance(metadata_date, datetime) else metadata_date
        date_source = metadata_date_source or "document_metadata"

    age_days, freshness_status, flags = freshness_for_date(doc_date, as_of_date=as_of_date)
    if date_source == "filename:date":
        flags = [*flags, "filename_date_inferred"]
    if evidence_type == EvidenceType.DOCUMENTED_INTENT:
        flags = [*flags, "documented_intent"]

    return EvidenceQuality(
        evidence_type=evidence_type,
        evidence_type_tags=evidence_type_tags or [evidence_type],
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
    types = sorted(
        {
            tag.value
            for match in matches
            for tag in (match.evidence_type_tags or [match.evidence_type])
        }
    )
    freshness = sorted({m.freshness_status.value for m in matches})
    return f"Evidence types: {', '.join(types)}. Freshness: {', '.join(freshness)}."
