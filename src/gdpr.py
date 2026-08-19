from __future__ import annotations

from dataclasses import dataclass


YES_NO_UNKNOWN = {"Yes", "No", "Unknown"}


@dataclass(frozen=True)
class GdprScopeTriage:
    candidate_status: str
    basis: tuple[str, ...]
    caveats: tuple[str, ...]


def triage_gdpr_article3(
    *,
    eu_establishment: str,
    offers_goods_services_to_people_in_eu: str,
    monitors_behaviour_in_eu: str,
    member_state_law_by_public_international_law: str = "Unknown",
) -> GdprScopeTriage:
    """Non-binding Article 3 scope triage.

    The helper is deliberately separate from the confirmed GDPR scope status used
    by the assessment engine. It never makes a legal determination for the user.
    """
    values = {
        "eu_establishment": eu_establishment,
        "offers_goods_services_to_people_in_eu": offers_goods_services_to_people_in_eu,
        "monitors_behaviour_in_eu": monitors_behaviour_in_eu,
        "member_state_law_by_public_international_law": member_state_law_by_public_international_law,
    }
    invalid = {key: value for key, value in values.items() if value not in YES_NO_UNKNOWN}
    if invalid:
        raise ValueError(f"GDPR Article 3 triage values must be Yes, No, or Unknown: {invalid}")

    basis: list[str] = []
    caveats: list[str] = [
        "This helper only triages the explicit territorial-scope triggers in GDPR Article 3 and is not legal advice.",
        "The confirmed GDPR scope field must be set separately before the engine treats GDPR controls as applicable or not applicable.",
    ]

    if eu_establishment == "Yes":
        basis.append("Article 3(1) indicator: processing in the context of an EU establishment is reported.")
    if offers_goods_services_to_people_in_eu == "Yes":
        basis.append("Article 3(2)(a) indicator: goods or services are offered to data subjects in the Union.")
    if monitors_behaviour_in_eu == "Yes":
        basis.append("Article 3(2)(b) indicator: behaviour of data subjects in the Union is monitored.")
    if member_state_law_by_public_international_law == "Yes":
        basis.append("Article 3(3) indicator: Member State law is reported to apply by public international law.")

    if basis:
        return GdprScopeTriage("candidate_in_scope", tuple(basis), tuple(caveats))

    if all(value == "No" for value in values.values()):
        basis.append("No Article 3(1), 3(2), or 3(3) trigger was identified from the supplied facts.")
        caveats.append("A qualified reviewer should confirm the supplied facts before recording GDPR as out of scope.")
        return GdprScopeTriage("no_article3_trigger_identified", tuple(basis), tuple(caveats))

    basis.append("One or more Article 3 facts remain unknown, so territorial scope cannot be triaged conclusively.")
    return GdprScopeTriage("insufficient_information", tuple(basis), tuple(caveats))
