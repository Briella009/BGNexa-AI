from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


DcpmiCandidateStatus = Literal["candidate_dcpmi", "no_trigger_identified", "review_required"]
DcpmiTier = Literal["UHL", "EHL", "OHL", "unknown"]

# GAID 2025, Schedule 7. Labels are normalised for application input; they are
# not substitutes for the source wording and must remain human-confirmed.
UHL_SPECIFIC_TYPES = {
    "commercial bank (national/regional)",
    "telecommunication company",
    "insurance company",
    "multinational company",
    "electricity distribution company",
    "oil and gas company",
    "public social media app provider",
    "public email app provider",
    "communication device manufacturer",
    "payment gateway service provider",
    "fintech",
}

EHL_SPECIFIC_TYPES = {
    "government mda",
    "microfinance bank",
    "higher institution",
    "secondary/tertiary hospital",
    "mortgage bank",
}

OHL_SPECIFIC_TYPES = {
    "primary/secondary school",
    "corporate training service provider",
    "primary health centre",
    "independent medical laboratory",
    "hotel/guest house under 50 suites",
}

# Schedule 7 paragraph 1 identifies these sectors as a DCPMI designation route,
# but the sector alone does not always resolve the UHL/EHL/OHL tier.
DESIGNATED_SECTORS = {
    "aviation",
    "communication",
    "education",
    "electric power",
    "export and import",
    "financial",
    "health",
    "hospitality",
    "insurance",
    "oil and gas",
    "tourism",
    "e-commerce",
    "public service",
}

TIER_ORDER = {"OHL": 1, "EHL": 2, "UHL": 3}


@dataclass(frozen=True)
class DcpmiTriageResult:
    candidate_status: DcpmiCandidateStatus
    candidate_tier: DcpmiTier
    basis: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    source_locator: str = "NDPC GAID 2025, Schedule 7"
    requires_human_confirmation: bool = True

    @property
    def is_candidate_dcpmi(self) -> bool:
        return self.candidate_status == "candidate_dcpmi"


def _normalise(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def triage_dcpmi(
    *,
    organisation_type: str | None = None,
    sector: str | None = None,
    data_subjects_six_months: int | None = None,
    commercial_ict_device_service: bool = False,
    sensitive_personal_data_commercial_subjects: int | None = None,
    processing_role: str = "Unsure",
) -> DcpmiTriageResult:
    """Provide a conservative, non-binding DCPMI triage result.

    This function intentionally does not return a legal Yes/No determination.
    It surfaces explicit Schedule 7 triggers and a candidate tier where the
    source text supports one. The organisation profile remains the authoritative
    user-confirmed input for control applicability.
    """

    if data_subjects_six_months is not None and data_subjects_six_months < 0:
        raise ValueError("data_subjects_six_months cannot be negative")
    if sensitive_personal_data_commercial_subjects is not None and sensitive_personal_data_commercial_subjects < 0:
        raise ValueError("sensitive_personal_data_commercial_subjects cannot be negative")

    org_type = _normalise(organisation_type)
    sector_value = _normalise(sector)
    role = _normalise(processing_role)

    tier_candidates: list[str] = []
    basis: list[str] = []
    ambiguities: list[str] = []
    candidate = False

    if org_type in UHL_SPECIFIC_TYPES:
        candidate = True
        tier_candidates.append("UHL")
        basis.append(f"Schedule 7 specifically lists {organisation_type} in the Ultra-High Level category.")
    elif org_type in EHL_SPECIFIC_TYPES:
        candidate = True
        tier_candidates.append("EHL")
        basis.append(f"Schedule 7 specifically lists {organisation_type} in the Extra-High Level category.")
    elif org_type in OHL_SPECIFIC_TYPES:
        candidate = True
        tier_candidates.append("OHL")
        basis.append(f"Schedule 7 specifically lists {organisation_type} in the Ordinary-High Level category.")

    if sector_value in DESIGNATED_SECTORS:
        candidate = True
        basis.append(
            f"Schedule 7 identifies the {sector} sector as a route to designation as a controller/processor of major importance."
        )
        if not tier_candidates:
            ambiguities.append("The broad sector trigger establishes a DCPMI indicator but does not, by itself, resolve the UHL/EHL/OHL tier.")

    if commercial_ict_device_service:
        candidate = True
        basis.append(
            "Schedule 7 identifies commercial ICT services on another individual's data-capable digital device as a DCPMI designation trigger."
        )
        if not tier_candidates:
            ambiguities.append("The commercial-ICT trigger does not, by itself, resolve the UHL/EHL/OHL tier.")

    if data_subjects_six_months is not None:
        count = data_subjects_six_months
        if count > 5000:
            candidate = True
            tier_candidates.append("UHL")
            basis.append("More than 5,000 data subjects processed within six months maps to the Schedule 7 UHL volume category.")
        elif 1000 < count < 5000:
            candidate = True
            tier_candidates.append("EHL")
            basis.append("More than 1,000 but fewer than 5,000 data subjects within six months maps to the Schedule 7 EHL volume category.")
        elif 200 < count < 1000:
            candidate = True
            tier_candidates.append("OHL")
            basis.append("More than 200 but fewer than 1,000 data subjects within six months maps to the Schedule 7 OHL volume category.")
        elif count in {1000, 5000}:
            candidate = True  # >200 designation threshold is still met.
            basis.append("The six-month volume exceeds the general 200-data-subject DCPMI designation threshold in Schedule 7.")
            ambiguities.append(
                f"Schedule 7's specific volume bands use 'over' and 'less than' wording that does not expressly allocate the exact boundary value {count:,}; tier requires human confirmation."
            )
        elif count > 200:
            candidate = True
            basis.append("The six-month volume exceeds the general 200-data-subject DCPMI designation threshold in Schedule 7.")
        else:
            basis.append("The supplied six-month volume does not exceed the Schedule 7 general threshold of 200 data subjects.")

    if sensitive_personal_data_commercial_subjects is not None and sensitive_personal_data_commercial_subjects > 200:
        if role in {"processor", "both"}:
            candidate = True
            tier_candidates.append("OHL")
            basis.append(
                "A processor handling sensitive personal data of more than 200 data subjects for commercial purposes is specifically listed in the Schedule 7 OHL category."
            )
        elif role == "unsure":
            candidate = True
            ambiguities.append(
                "Sensitive-personal-data volume may trigger the specific OHL processor category, but processing role is marked Unsure."
            )
        else:
            ambiguities.append(
                "The specific Schedule 7 sensitive-data OHL wording is framed for processors; this profile is not marked as a processor."
            )

    if tier_candidates:
        candidate_tier: DcpmiTier = max(tier_candidates, key=lambda tier: TIER_ORDER[tier])  # type: ignore[assignment]
        if len(set(tier_candidates)) > 1:
            ambiguities.append(
                "Multiple Schedule 7 classification routes apply; this triage shows the highest indicated tier and requires confirmation."
            )
    else:
        candidate_tier = "unknown"

    if candidate:
        return DcpmiTriageResult(
            candidate_status="candidate_dcpmi",
            candidate_tier=candidate_tier,
            basis=basis,
            ambiguities=ambiguities,
        )

    if not any(
        [
            org_type,
            sector_value,
            data_subjects_six_months is not None,
            commercial_ict_device_service,
            sensitive_personal_data_commercial_subjects is not None,
        ]
    ):
        return DcpmiTriageResult(
            candidate_status="review_required",
            candidate_tier="unknown",
            basis=[],
            ambiguities=["Insufficient information was supplied for Schedule 7 triage."],
        )

    return DcpmiTriageResult(
        candidate_status="no_trigger_identified",
        candidate_tier="unknown",
        basis=basis,
        ambiguities=[
            "No explicit trigger was identified from the supplied fields. This is not a legal finding that the organisation is outside DCPMI scope; other Schedule 7 facts may change the result."
        ],
    )
