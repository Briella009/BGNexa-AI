from __future__ import annotations

from collections import defaultdict

from .models import Framework


def capability_crosswalk(frameworks: list[Framework]) -> list[dict[str, object]]:
    """Build a transparent semantic crosswalk from shared capability tags.

    This is not a claim of legal, regulatory, or control equivalence. It only
    shows that controls share a security/privacy capability topic and may benefit
    from some common evidence.
    """
    buckets: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for framework in frameworks:
        for control in framework.controls:
            for tag in control.capability_tags:
                buckets[tag].append((framework.framework_id, control.control_id, control.reference))

    rows: list[dict[str, object]] = []
    for tag, entries in buckets.items():
        unique_frameworks = sorted({entry[0] for entry in entries})
        if len(unique_frameworks) < 2:
            continue
        rows.append(
            {
                "capability": tag,
                "framework_count": len(unique_frameworks),
                "control_count": len(entries),
                "frameworks": ", ".join(unique_frameworks),
                "control_references": "; ".join(f"{f}:{ref}" for f, _, ref in entries),
                "evidence_reuse_opportunity": (
                    "Potential shared evidence area: inspect whether one evidence set can support multiple requirements."
                ),
                "note": "Shared capability only; not a declaration of control equivalence.",
            }
        )

    # Put the broadest potential reuse areas first without implying legal importance.
    return sorted(rows, key=lambda row: (-int(row["framework_count"]), -int(row["control_count"]), str(row["capability"])))


def evidence_reuse_opportunities(frameworks: list[Framework], limit: int = 10) -> list[dict[str, object]]:
    """Return the highest-overlap capability topics for UI/report prioritisation.

    Ranking reflects only the number of mapped frameworks/controls. It is not a
    risk score, compliance priority, or assertion that the requirements match.
    """
    return capability_crosswalk(frameworks)[: max(limit, 0)]
