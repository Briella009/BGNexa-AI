from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .models import Framework


AUTHORITY_HOSTS = {
    "Central Bank of Nigeria": ("cbn.gov.ng",),
    "Nigeria Data Protection Commission": ("ndpc.gov.ng",),
    "ISO/IEC": ("iso.org",),
    "National Institute of Standards and Technology (NIST)": ("nist.gov",),
    "European Union (EUR-Lex)": ("eur-lex.europa.eu",),
}


@dataclass(frozen=True)
class ProvenanceFinding:
    framework_id: str
    severity: str
    message: str


def _host_matches(host: str, allowed: tuple[str, ...]) -> bool:
    host = host.lower().split(":", 1)[0]
    return any(host == item or host.endswith(f".{item}") for item in allowed)


def verification_tier(status: str) -> str:
    value = status.lower()
    if value in {"official_text_cross_checked", "official_reference_paraphrase", "direct_authority_pdf_verified", "direct_authority_pdf_verified_user_supplied_scan"}:
        return "authority_traceable"
    if "authority_document_cross_checked" in value:
        return "authority_metadata_plus_archival_text"
    if "pending_direct" in value:
        return "authority_metadata_plus_secondary_text_pending_direct"
    if "official" in value or "authority" in value:
        return "authority_traceable"
    return "unknown"


def audit_framework_provenance(frameworks: dict[str, Framework]) -> list[ProvenanceFinding]:
    findings: list[ProvenanceFinding] = []
    for framework in frameworks.values():
        parsed = urlparse(framework.source.source_url)
        allowed = AUTHORITY_HOSTS.get(framework.authority)
        if not parsed.scheme.startswith("http") or not parsed.netloc:
            findings.append(
                ProvenanceFinding(framework.framework_id, "error", "Framework source URL is not a valid HTTP(S) URL.")
            )
        elif allowed and not _host_matches(parsed.netloc, allowed):
            findings.append(
                ProvenanceFinding(
                    framework.framework_id,
                    "error",
                    f"Primary source host {parsed.netloc!r} does not match expected authority domain(s): {', '.join(allowed)}.",
                )
            )

        if not framework.source.last_verified:
            findings.append(ProvenanceFinding(framework.framework_id, "error", "Framework has no last_verified date."))

        for control in framework.controls:
            tier = verification_tier(control.verification_status)
            if tier == "unknown":
                findings.append(
                    ProvenanceFinding(
                        framework.framework_id,
                        "error",
                        f"{control.control_id} has an unrecognised verification status: {control.verification_status}",
                    )
                )
            elif tier.endswith("pending_direct"):
                findings.append(
                    ProvenanceFinding(
                        framework.framework_id,
                        "warning",
                        f"{control.control_id} is traceable but still pending direct paragraph-level authority-file verification.",
                    )
                )
            if not control.source_locator.strip():
                findings.append(
                    ProvenanceFinding(framework.framework_id, "error", f"{control.control_id} has no source locator.")
                )
            if not control.requirement_summary.strip():
                findings.append(
                    ProvenanceFinding(framework.framework_id, "error", f"{control.control_id} has no requirement summary.")
                )
    return findings


def provenance_summary(frameworks: dict[str, Framework]) -> dict[str, object]:
    findings = audit_framework_provenance(frameworks)
    tiers: dict[str, int] = {}
    total_controls = 0
    for framework in frameworks.values():
        for control in framework.controls:
            total_controls += 1
            tier = verification_tier(control.verification_status)
            tiers[tier] = tiers.get(tier, 0) + 1
    return {
        "frameworks": len(frameworks),
        "controls": total_controls,
        "verification_tiers": tiers,
        "errors": sum(1 for f in findings if f.severity == "error"),
        "warnings": sum(1 for f in findings if f.severity == "warning"),
        "findings": [f.__dict__ for f in findings],
    }
