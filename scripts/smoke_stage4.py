from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.applicability import resolve_control_applicability
from src.evaluation import run_retrieval_evaluation, run_security_evaluation
from src.framework_loader import load_frameworks
from src.gdpr import triage_gdpr_article3
from src.models import AssessmentStatus
from src.provenance import provenance_summary


def main() -> int:
    frameworks = load_frameworks(ROOT / "frameworks")
    retrieval = run_retrieval_evaluation(
        frameworks_dir=ROOT / "frameworks",
        fixtures_dir=ROOT / "evals" / "fixtures",
        cases_path=ROOT / "evals" / "retrieval_cases.yaml",
    )
    provenance = provenance_summary(frameworks)
    security = run_security_evaluation(
        fixtures_dir=ROOT / "evals" / "fixtures",
        frameworks_dir=ROOT / "frameworks",
    )

    triage = triage_gdpr_article3(
        eu_establishment="No",
        offers_goods_services_to_people_in_eu="Yes",
        monitors_behaviour_in_eu="No",
        member_state_law_by_public_international_law="No",
    )
    gdpr_security = next(c for c in frameworks["gdpr-2016-679"].controls if c.control_id == "GDPR-32")
    unknown_scope = resolve_control_applicability(
        framework_id="gdpr-2016-679",
        control=gdpr_security,
        dcpmi_status="No",
        processing_role="Controller",
        gdpr_scope_status="Unknown",
    )

    print(
        "stage4 "
        f"frameworks={len(frameworks)} "
        f"controls={sum(len(f.controls) for f in frameworks.values())} "
        f"nist_subcategories={len(frameworks['nist-csf-2.0'].controls)} "
        f"gdpr_seed_controls={len(frameworks['gdpr-2016-679'].controls)} "
        f"ofi_verified_controls={len(frameworks['cbn-ofi-2022'].controls)}"
    )
    print(
        f"retrieval cases={retrieval['cases']} recall_at_1={retrieval['recall_at_1']:.4f} "
        f"recall_at_3={retrieval['recall_at_3']:.4f} mrr={retrieval['mrr']:.4f}"
    )
    print(
        f"gdpr_triage={triage.candidate_status} "
        f"unknown_scope_guard={unknown_scope.status.value if unknown_scope else 'missing'}"
    )
    print(f"provenance_errors={provenance['errors']} provenance_warnings={provenance['warnings']} security_pass={security['pass']}")

    failed = (
        len(frameworks["nist-csf-2.0"].controls) != 106
        or len(frameworks["gdpr-2016-679"].controls) != 18
        or not all(c.source_pdf_pages for c in frameworks["cbn-ofi-2022"].controls)
        or triage.candidate_status != "candidate_in_scope"
        or unknown_scope is None
        or unknown_scope.status != AssessmentStatus.REVIEW_REQUIRED
        or retrieval["recall_at_3"] < 0.90
        or retrieval["mrr"] < 0.75
        or provenance["errors"] > 0
        or provenance["warnings"] > 0
        or not security["pass"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
