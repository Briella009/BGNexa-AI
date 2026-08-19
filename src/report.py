from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd

from .crosswalk import evidence_reuse_opportunities
from .models import AssessmentResult, AssessmentStatus, Framework


def results_dataframe(framework: Framework, results: list[AssessmentResult]) -> pd.DataFrame:
    controls = {c.control_id: c for c in framework.controls}
    rows = []
    for result in results:
        control = controls[result.control_id]
        rows.append(
            {
                "framework": framework.name,
                "framework_type": framework.framework_type,
                "control_id": control.control_id,
                "reference": control.reference,
                "title": control.title,
                "status": result.status.value,
                "evidence_strength": result.evidence_strength,
                "human_validated": result.human_validated,
                "reviewer": result.reviewer or "",
                "reviewed_at": result.reviewed_at or "",
                "rationale": result.rationale,
                "reviewer_note": result.reviewer_note or "",
                "recommendation": result.recommendation or "",
                "evidence_sources": "; ".join(
                    f"{e.source_name}{f' p.{e.page}' if e.page else ''}" for e in result.evidence
                ),
                "retrieval_methods": "; ".join(sorted({e.retrieval_method for e in result.evidence})),
                "source_locator": control.source_locator,
                "verification_status": control.verification_status,
            }
        )
    return pd.DataFrame(rows)


def priority_gaps_dataframe(bundle: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in bundle.values():
        framework: Framework = item["framework"]
        control_map = {c.control_id: c for c in framework.controls}
        for result in item["results"]:
            if result.status not in {
                AssessmentStatus.NOT_EVIDENCED,
                AssessmentStatus.PARTIAL,
                AssessmentStatus.REVIEW_REQUIRED,
            }:
                continue
            control = control_map[result.control_id]
            if result.status == AssessmentStatus.REVIEW_REQUIRED:
                # Unresolved evidence/applicability is a review task, not a confirmed gap.
                priority = "Review"
                rank = 4
            elif result.status == AssessmentStatus.NOT_EVIDENCED and control.weight >= 1.8:
                priority = "Critical"
                rank = 1
            elif result.status == AssessmentStatus.NOT_EVIDENCED:
                priority = "High"
                rank = 2
            elif result.status == AssessmentStatus.PARTIAL and control.weight >= 1.5:
                priority = "High"
                rank = 2
            else:
                priority = "Medium"
                rank = 3
            rows.append(
                {
                    "priority": priority,
                    "priority_rank": rank,
                    "framework": framework.name,
                    "framework_type": framework.framework_type,
                    "reference": control.reference,
                    "control": control.title,
                    "status": result.status.value,
                    "weight": control.weight,
                    "recommendation": result.recommendation or "Perform qualified human review.",
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=["priority", "framework", "framework_type", "reference", "control", "status", "recommendation"]
        )
    df = pd.DataFrame(rows).sort_values(["priority_rank", "weight", "framework"], ascending=[True, False, True])
    return df.drop(columns=["priority_rank"]).reset_index(drop=True)


def build_executive_html(bundle: dict[str, dict[str, Any]], organisation_name: str = "Organisation") -> str:
    framework_rows = []
    frameworks: list[Framework] = []
    for item in bundle.values():
        fw: Framework = item["framework"]
        frameworks.append(fw)
        score = item["score"]
        readiness = (
            "Not yet resolved"
            if score.provisional_readiness_percent is None
            else f"{score.provisional_readiness_percent:.1f}%"
        )
        framework_rows.append(
            f"<tr><td>{escape(fw.name)}</td><td>{escape(fw.framework_type)}</td>"
            f"<td>{escape(readiness)}</td><td>{score.coverage_percent:.1f}%</td>"
            f"<td>{score.supported}</td><td>{score.partial}</td><td>{score.not_evidenced}</td><td>{score.review_required}</td></tr>"
        )

    gaps = priority_gaps_dataframe(bundle)
    gap_rows = []
    for _, row in gaps.head(15).iterrows():
        gap_rows.append(
            "<tr>"
            f"<td>{escape(str(row['priority']))}</td>"
            f"<td>{escape(str(row['framework']))}</td>"
            f"<td>{escape(str(row['reference']))}</td>"
            f"<td>{escape(str(row['control']))}</td>"
            f"<td>{escape(str(row['recommendation']))}</td>"
            "</tr>"
        )

    reuse_rows = []
    for row in evidence_reuse_opportunities(frameworks, limit=8):
        reuse_rows.append(
            "<tr>"
            f"<td>{escape(str(row['capability']))}</td>"
            f"<td>{row['framework_count']}</td>"
            f"<td>{row['control_count']}</td>"
            f"<td>{escape(str(row['frameworks']))}</td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cybersecurity Readiness Report - {escape(organisation_name)}</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#18212f;line-height:1.5}}
h1{{margin-bottom:4px}} .muted{{color:#596579}} .notice{{padding:14px 16px;background:#f4f6f8;border-left:4px solid #596579;margin:20px 0}}
table{{border-collapse:collapse;width:100%;margin:14px 0 28px}} th,td{{border:1px solid #d9dee5;padding:10px;text-align:left;vertical-align:top}} th{{background:#f4f6f8}}
h2{{margin-top:34px}} footer{{margin-top:40px;padding-top:14px;border-top:1px solid #d9dee5;color:#596579;font-size:13px}}
</style></head><body>
<h1>BGNexa AI</h1>
<p class="muted">Executive readiness report for {escape(organisation_name)}</p>
<div class="notice"><strong>Important:</strong> This report is evidence-backed readiness analysis only. Laws, regulatory frameworks, voluntary guidance and international standards are kept as distinct source types. This report is not a legal-compliance determination, ISO certification, regulator approval, or audit opinion.</div>
<h2>Framework summary</h2>
<table><thead><tr><th>Framework</th><th>Type</th><th>Provisional readiness</th><th>Resolved coverage</th><th>Supported</th><th>Partial</th><th>Not evidenced</th><th>Review required</th></tr></thead>
<tbody>{''.join(framework_rows)}</tbody></table>
<h2>Priority gaps</h2>
<table><thead><tr><th>Priority</th><th>Framework</th><th>Reference</th><th>Control</th><th>Recommended next step</th></tr></thead>
<tbody>{''.join(gap_rows) if gap_rows else '<tr><td colspan="5">No unresolved gaps in the current assessment set.</td></tr>'}</tbody></table>
<h2>Potential evidence reuse</h2>
<p class="muted">These are shared capability topics only. They are not cross-framework equivalence mappings and do not mean satisfying one requirement satisfies another.</p>
<table><thead><tr><th>Capability</th><th>Frameworks</th><th>Mapped controls</th><th>Framework IDs</th></tr></thead>
<tbody>{''.join(reuse_rows) if reuse_rows else '<tr><td colspan="4">Select multiple framework packs to identify overlap areas.</td></tr>'}</tbody></table>
<footer>Generated by BGNexa AI. Validate findings with qualified cybersecurity, privacy, legal, regulatory, and audit personnel before reliance.</footer>
</body></html>"""
