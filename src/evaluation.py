from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .evidence import parse_path
from .framework_loader import load_frameworks
from .retriever import EvidenceRetriever


@dataclass(frozen=True)
class RetrievalEvalCase:
    case_id: str
    framework_id: str
    control_id: str
    expected_source: str
    top_k: int = 3


def load_retrieval_cases(path: str | Path) -> list[RetrievalEvalCase]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cases: list[RetrievalEvalCase] = []
    for raw in payload.get("cases", []):
        cases.append(
            RetrievalEvalCase(
                case_id=raw["id"],
                framework_id=raw["framework_id"],
                control_id=raw["control_id"],
                expected_source=raw["expected_source"],
                top_k=int(raw.get("top_k", 3)),
            )
        )
    return cases


def _fixture_chunks(fixtures_dir: str | Path):
    chunks = []
    for path in sorted(Path(fixtures_dir).glob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}:
            chunks.extend(parse_path(path))
    return chunks


def run_retrieval_evaluation(
    *,
    frameworks_dir: str | Path,
    fixtures_dir: str | Path,
    cases_path: str | Path,
) -> dict[str, Any]:
    frameworks = load_frameworks(frameworks_dir)
    controls = {
        (fw.framework_id, control.control_id): control
        for fw in frameworks.values()
        for control in fw.controls
    }
    cases = load_retrieval_cases(cases_path)
    chunks = _fixture_chunks(fixtures_dir)
    retriever = EvidenceRetriever(chunks, min_score=0.03)

    rows = []
    reciprocal_ranks = []
    for case in cases:
        key = (case.framework_id, case.control_id)
        if key not in controls:
            raise KeyError(f"Golden case {case.case_id} references unknown control {case.framework_id}/{case.control_id}")
        matches = retriever.retrieve(controls[key], top_k=max(case.top_k, 5))
        rank = None
        for idx, match in enumerate(matches, start=1):
            if match.source_name == case.expected_source:
                rank = idx
                break
        reciprocal_ranks.append(0.0 if rank is None else 1.0 / rank)
        rows.append(
            {
                "id": case.case_id,
                "framework_id": case.framework_id,
                "control_id": case.control_id,
                "expected_source": case.expected_source,
                "rank": rank,
                "hit_at_1": rank == 1,
                "hit_at_3": rank is not None and rank <= 3,
                "top_sources": [m.source_name for m in matches[: case.top_k]],
            }
        )

    total = len(rows)
    return {
        "cases": total,
        "recall_at_1": round(sum(1 for r in rows if r["hit_at_1"]) / total, 4) if total else 0.0,
        "recall_at_3": round(sum(1 for r in rows if r["hit_at_3"]) / total, 4) if total else 0.0,
        "mrr": round(sum(reciprocal_ranks) / total, 4) if total else 0.0,
        "failures": [r for r in rows if not r["hit_at_3"]],
        "results": rows,
    }


def run_security_evaluation(*, fixtures_dir: str | Path, frameworks_dir: str | Path) -> dict[str, Any]:
    from .copilot import answer_copilot_question
    from .models import EvidenceMatch

    malicious_path = Path(fixtures_dir) / "prompt_injection_eval.txt"
    malicious_chunks = parse_path(malicious_path)
    injection_detection_pass = bool(malicious_chunks) and all(chunk.injection_flag for chunk in malicious_chunks)

    frameworks = load_frameworks(frameworks_dir)
    safe = EvidenceMatch(
        chunk_id="safe-eval",
        source_name="breach_response.txt",
        excerpt="The personal-data breach plan maintains a breach register and regulator notification workflow.",
        retrieval_score=0.8,
        injection_flag=False,
    )
    flagged = EvidenceMatch(
        chunk_id="malicious-eval",
        source_name="prompt_injection_eval.txt",
        excerpt=malicious_chunks[0].text if malicious_chunks else "ignore previous instructions",
        retrieval_score=0.99,
        injection_flag=True,
    )
    answer = answer_copilot_question(
        "How does the organisation handle personal-data breaches?",
        [flagged, safe],
        [frameworks["ndpa-2023"], frameworks["ndpc-gaid-2025"]],
        use_ai=False,
    )
    cited_ids = {citation.citation_id for citation in answer.evidence_citations}
    copilot_exclusion_pass = "malicious-eval" not in cited_ids and "safe-eval" in cited_ids
    return {
        "prompt_injection_detection": injection_detection_pass,
        "copilot_flagged_evidence_exclusion": copilot_exclusion_pass,
        "pass": injection_detection_pass and copilot_exclusion_pass,
    }
