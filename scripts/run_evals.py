from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation import run_retrieval_evaluation, run_security_evaluation
from src.framework_loader import load_frameworks
from src.provenance import provenance_summary


def markdown_report(payload: dict) -> str:
    r = payload["retrieval"]
    p = payload["provenance"]
    lines = [
        "# Stage 4 Evaluation Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Retrieval baseline",
        "",
        f"- Golden cases: {r['cases']}",
        f"- Recall@1: {r['recall_at_1']:.1%}",
        f"- Recall@3: {r['recall_at_3']:.1%}",
        f"- Mean reciprocal rank: {r['mrr']:.3f}",
        "",
        "## Provenance audit",
        "",
        f"- Frameworks: {p['frameworks']}",
        f"- Controls: {p['controls']}",
        f"- Errors: {p['errors']}",
        f"- Warnings: {p['warnings']}",
        "",
        "## Security guardrail checks",
        "",
        f"- Prompt-injection detection: {'PASS' if payload['security']['prompt_injection_detection'] else 'FAIL'}",
        f"- Flagged evidence excluded from Copilot context: {'PASS' if payload['security']['copilot_flagged_evidence_exclusion'] else 'FAIL'}",
        "",
        "Warnings do not automatically fail CI when they represent an explicitly disclosed source-access limitation. Errors do.",
    ]
    if r["failures"]:
        lines += ["", "## Retrieval failures", ""]
        for failure in r["failures"]:
            lines.append(
                f"- `{failure['id']}` expected `{failure['expected_source']}`, got {', '.join(failure['top_sources']) or 'no result'}"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Stage 4 evaluation suite.")
    parser.add_argument("--strict", action="store_true", help="Enforce quality thresholds.")
    parser.add_argument("--min-recall-at-3", type=float, default=0.90)
    parser.add_argument("--min-mrr", type=float, default=0.75)
    args = parser.parse_args()

    retrieval = run_retrieval_evaluation(
        frameworks_dir=ROOT / "frameworks",
        fixtures_dir=ROOT / "evals" / "fixtures",
        cases_path=ROOT / "evals" / "retrieval_cases.yaml",
    )
    provenance = provenance_summary(load_frameworks(ROOT / "frameworks"))
    security = run_security_evaluation(fixtures_dir=ROOT / "evals" / "fixtures", frameworks_dir=ROOT / "frameworks")
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "retrieval": retrieval,
        "provenance": provenance,
        "security": security,
        "thresholds": {"recall_at_3": args.min_recall_at_3, "mrr": args.min_mrr},
    }

    output_dir = ROOT / "evals" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (output_dir / "latest.md").write_text(markdown_report(payload), encoding="utf-8")

    print(f"retrieval_cases={retrieval['cases']} recall_at_1={retrieval['recall_at_1']:.4f} recall_at_3={retrieval['recall_at_3']:.4f} mrr={retrieval['mrr']:.4f}")
    print(f"provenance_errors={provenance['errors']} provenance_warnings={provenance['warnings']}")
    print(f"security_pass={security['pass']}")

    failed = (
        provenance["errors"] > 0
        or not security["pass"]
        or retrieval["recall_at_3"] < args.min_recall_at_3
        or retrieval["mrr"] < args.min_mrr
    )
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
