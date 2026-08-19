from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation import run_retrieval_evaluation, run_security_evaluation
from src.framework_loader import load_frameworks
from src.provenance import provenance_summary


def main() -> int:
    retrieval = run_retrieval_evaluation(
        frameworks_dir=ROOT / "frameworks",
        fixtures_dir=ROOT / "evals" / "fixtures",
        cases_path=ROOT / "evals" / "retrieval_cases.yaml",
    )
    provenance = provenance_summary(load_frameworks(ROOT / "frameworks"))
    security = run_security_evaluation(
        fixtures_dir=ROOT / "evals" / "fixtures",
        frameworks_dir=ROOT / "frameworks",
    )

    print(
        "stage3 "
        f"cases={retrieval['cases']} "
        f"recall_at_1={retrieval['recall_at_1']:.4f} "
        f"recall_at_3={retrieval['recall_at_3']:.4f} "
        f"mrr={retrieval['mrr']:.4f}"
    )
    print(
        "provenance "
        f"frameworks={provenance['frameworks']} "
        f"controls={provenance['controls']} "
        f"errors={provenance['errors']} "
        f"warnings={provenance['warnings']}"
    )
    print(f"security_pass={security['pass']}")

    failed = (
        retrieval["recall_at_3"] < 0.90
        or retrieval["mrr"] < 0.75
        or provenance["errors"] > 0
        or not security["pass"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
