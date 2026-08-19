from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class AuthorityPdfSpec:
    framework_id: str
    expected_title_fragment: str
    markers: tuple[str, ...]
    min_pages: int


SPECS = {
    "cbn-dmb-psb-2024": AuthorityPdfSpec(
        framework_id="cbn-dmb-psb-2024",
        expected_title_fragment="deposit money banks and payment service banks",
        markers=(
            "risk-based cybersecurity framework",
            "cybersecurity self-assessment",
            "cyber-threat intelligence",
            "emerging technologies",
            "security incident reporting template",
            "artificial intelligence and machine learning",
        ),
        min_pages=20,
    ),
    "cbn-ofi-2022": AuthorityPdfSpec(
        framework_id="cbn-ofi-2022",
        expected_title_fragment="other financial institutions",
        markers=(
            "risk-based cybersecurity framework",
            "cybersecurity risk management system",
            "cyber-threat intelligence",
            "metrics, monitoring",
            "january 1, 2023",
        ),
        min_pages=20,
    ),
}


def _normalise(text: str) -> str:
    text = text.casefold()
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_extracted_authority_text(framework_id: str, text: str, *, page_count: int) -> dict[str, object]:
    if framework_id not in SPECS:
        raise KeyError(f"No direct-authority PDF verification specification for {framework_id}")
    spec = SPECS[framework_id]
    normalised = _normalise(text)
    markers = {marker: _normalise(marker) in normalised for marker in spec.markers}
    title_match = _normalise(spec.expected_title_fragment) in normalised
    page_count_ok = page_count >= spec.min_pages
    missing_markers = [marker for marker, found in markers.items() if not found]
    passed = title_match and page_count_ok and not missing_markers
    if passed:
        message = (
            "A passing structural check confirms that the supplied PDF resembles the expected framework. "
            "It does not prove provenance by itself; retain the original authority source and review the file manually before upgrading source status."
        )
    else:
        reasons: list[str] = []
        if not title_match:
            reasons.append("expected title fragment was not found")
        if not page_count_ok:
            reasons.append(f"page count is below the expected minimum of {spec.min_pages}")
        if missing_markers:
            reasons.append("required structural markers are missing")
        message = "Structural verification failed; do not upgrade the source verification tier. " + "; ".join(reasons) + "."
    return {
        "framework_id": framework_id,
        "passed": passed,
        "verification_mode": "text_layer_structural_check",
        "manual_visual_verification_required": False,
        "title_match": title_match,
        "page_count": page_count,
        "minimum_pages": spec.min_pages,
        "page_count_ok": page_count_ok,
        "markers": markers,
        "missing_markers": missing_markers,
        "warning": message,
    }


def verify_manual_visual_observations(
    framework_id: str,
    *,
    observed_text: str,
    page_count: int,
) -> dict[str, object]:
    """Validate a documented human/render review against the same structural spec.

    This is intended for image-only authority PDFs where text extraction cannot be
    relied upon. The caller is responsible for performing and documenting the page
    review; this function only applies deterministic marker checks to those recorded
    observations.
    """
    result = verify_extracted_authority_text(framework_id, observed_text, page_count=page_count)
    result["verification_mode"] = "manual_visual_render_review"
    result["manual_visual_verification_required"] = False
    result["warning"] = (
        "Recorded visual observations match the expected authority-document structure. "
        "Retain the source hash, page count, review date, and provenance record; do not redistribute restricted source material."
        if result["passed"]
        else "Recorded visual observations did not satisfy the authority-document structural specification; do not upgrade source status."
    )
    return result


def verify_authority_pdf(framework_id: str, pdf_path: str | Path) -> dict[str, object]:
    path = Path(pdf_path)
    raw = path.read_bytes()
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not _normalise(text):
        spec = SPECS[framework_id]
        result = {
            "framework_id": framework_id,
            "passed": False,
            "verification_mode": "image_only_pdf",
            "manual_visual_verification_required": True,
            "title_match": None,
            "page_count": len(reader.pages),
            "minimum_pages": spec.min_pages,
            "page_count_ok": len(reader.pages) >= spec.min_pages,
            "markers": {},
            "missing_markers": list(spec.markers),
            "warning": (
                "No usable PDF text layer was found. This is not a source-verification failure: perform a full render/visual review "
                "and record the observations before upgrading the verification tier."
            ),
        }
    else:
        result = verify_extracted_authority_text(framework_id, text, page_count=len(reader.pages))
    result.update(
        {
            "file_name": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    )
    return result
