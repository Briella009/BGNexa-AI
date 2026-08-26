from __future__ import annotations

import hashlib
import io
from datetime import date, datetime
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .evidence_quality import EvidenceQuality, build_evidence_quality
from .models import EvidenceChunk
from .security import contains_prompt_injection


def _metadata_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return None


def _chunk_text(
    text: str,
    source_name: str,
    page: int | None = None,
    size: int = 1200,
    overlap: int = 180,
    quality: EvidenceQuality | None = None,
) -> list[EvidenceChunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    quality = quality or build_evidence_quality(source_name, cleaned)
    chunks: list[EvidenceChunk] = []
    start = 0
    index = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        chunk = cleaned[start:end]
        chunks.append(
            EvidenceChunk(
                chunk_id=f"{source_name}:{page or 0}:{index}",
                source_name=source_name,
                page=page,
                text=chunk,
                injection_flag=contains_prompt_injection(chunk),
                content_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                evidence_type=quality.evidence_type,
                evidence_type_reason=quality.evidence_type_reason,
                document_date=quality.document_date,
                date_source=quality.date_source,
                age_days=quality.age_days,
                freshness_status=quality.freshness_status,
                quality_flags=list(quality.quality_flags),
            )
        )
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
        index += 1
    return chunks


def parse_bytes(filename: str, content: bytes, *, as_of_date: date | None = None) -> list[EvidenceChunk]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        page_texts = [page.extract_text() or "" for page in reader.pages]
        source_text = "\n".join(page_texts[:10])
        metadata_date = None
        metadata_source = None
        metadata = reader.metadata
        if metadata is not None:
            metadata_date = _metadata_datetime(getattr(metadata, "modification_date", None))
            metadata_source = "pdf_metadata:modified" if metadata_date else None
            if metadata_date is None:
                metadata_date = _metadata_datetime(getattr(metadata, "creation_date", None))
                metadata_source = "pdf_metadata:created" if metadata_date else None
        quality = build_evidence_quality(
            filename,
            source_text,
            metadata_date=metadata_date,
            metadata_date_source=metadata_source,
            as_of_date=as_of_date,
        )
        chunks: list[EvidenceChunk] = []
        for i, text in enumerate(page_texts, start=1):
            chunks.extend(_chunk_text(text, filename, page=i, quality=quality))
        return chunks

    if suffix == ".docx":
        document = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in document.paragraphs)
        metadata_date = _metadata_datetime(document.core_properties.modified)
        metadata_source = "docx_metadata:modified" if metadata_date else None
        if metadata_date is None:
            metadata_date = _metadata_datetime(document.core_properties.created)
            metadata_source = "docx_metadata:created" if metadata_date else None
        quality = build_evidence_quality(
            filename,
            text,
            metadata_date=metadata_date,
            metadata_date_source=metadata_source,
            as_of_date=as_of_date,
        )
        return _chunk_text(text, filename, quality=quality)

    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
        quality = build_evidence_quality(filename, text, as_of_date=as_of_date)
        return _chunk_text(text, filename, quality=quality)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def parse_path(path: str | Path, *, as_of_date: date | None = None) -> list[EvidenceChunk]:
    path = Path(path)
    return parse_bytes(path.name, path.read_bytes(), as_of_date=as_of_date)
