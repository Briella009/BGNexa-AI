from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.applicability import resolve_control_applicability
from src.assessor import assess_control
from src.evidence import parse_path
from src.framework_loader import load_frameworks
from src.report import build_executive_html, priority_gaps_dataframe
from src.retriever import HybridEvidenceRetriever
from src.review import build_assessment_snapshot, verify_snapshot_digest
from src.scoring import calculate_score


OUTPUT = ROOT / "demo_outputs"


def main() -> None:
    frameworks = load_frameworks(ROOT / "frameworks")
    selected = [frameworks["ndpa-2023"], frameworks["iso-iec-27001-2022-amd1-2024"]]

    chunks = []
    for name in ["access_control_policy.txt", "incident_response_policy.txt", "privacy_governance.txt"]:
        chunks.extend(parse_path(ROOT / "sample_data" / name))

    retriever = HybridEvidenceRetriever(chunks)
    bundle = {}
    for framework in selected:
        results = []
        for control in framework.controls:
            applicability = resolve_control_applicability(
                framework_id=framework.framework_id,
                control=control,
                dcpmi_status="Unknown",
                processing_role="Both",
            )
            if applicability is not None:
                results.append(applicability)
            else:
                results.append(
                    assess_control(
                        framework.framework_id,
                        control,
                        retriever.retrieve(control, top_k=5),
                        use_ai=False,
                    )
                )
        bundle[framework.framework_id] = {
            "framework": framework,
            "results": results,
            "score": calculate_score(framework.controls, results),
        }

    OUTPUT.mkdir(exist_ok=True)
    report_path = OUTPUT / "offline_readiness_report.html"
    snapshot_path = OUTPUT / "offline_readiness_snapshot.json"
    gaps_path = OUTPUT / "offline_priority_queue.csv"

    report_path.write_text(build_executive_html(bundle, "Demo Organisation"), encoding="utf-8")
    snapshot = build_assessment_snapshot(
        bundle,
        organisation_profile={
            "organisation_name": "Demo Organisation",
            "processing_role": "Both",
            "dcpmi_status": "Unknown",
        },
    )
    snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    priority_gaps_dataframe(bundle).to_csv(gaps_path, index=False)

    print(f"retrieval_mode={retriever.mode}")
    for framework_id, item in bundle.items():
        score = item["score"]
        print(
            f"{framework_id}: readiness={score.provisional_readiness_percent} "
            f"coverage={score.coverage_percent:.1f}% review_required={score.review_required}"
        )
    print(f"snapshot_digest_valid={verify_snapshot_digest(snapshot)}")
    print(f"report={report_path}")
    print(f"snapshot={snapshot_path}")
    print(f"priority_queue={gaps_path}")


if __name__ == "__main__":
    main()
