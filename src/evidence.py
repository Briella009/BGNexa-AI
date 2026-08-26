from __future__ import annotations

import hashlib
import io
from datetime import date, datetime
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .evidence_quality import EvidenceQuality, build_evidence_quality
from .models import EvidenceChunk, EvidenceSourceRecord, EvidenceType, FreshnessStatus
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
    source_hash: str | None = None,
    source_size_bytes: int | None = None,
    source_extension: str | None = None,
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
                source_hash=source_hash,
                source_size_bytes=source_size_bytes,
                source_extension=source_extension,
                evidence_type=quality.evidence_type,
                evidence_type_tags=list(quality.evidence_type_tags),
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
    source_hash = hashlib.sha256(content).hexdigest()
    source_size_bytes = len(content)

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
            chunks.extend(
                _chunk_text(
                    text,
                    filename,
                    page=i,
                    quality=quality,
                    source_hash=source_hash,
                    source_size_bytes=source_size_bytes,
                    source_extension=suffix,
                )
            )
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
        return _chunk_text(
            text,
            filename,
            quality=quality,
            source_hash=source_hash,
            source_size_bytes=source_size_bytes,
            source_extension=suffix,
        )

    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
        quality = build_evidence_quality(filename, text, as_of_date=as_of_date)
        return _chunk_text(
            text,
            filename,
            quality=quality,
            source_hash=source_hash,
            source_size_bytes=source_size_bytes,
            source_extension=suffix,
        )

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def parse_path(path: str | Path, *, as_of_date: date | None = None) -> list[EvidenceChunk]:
    path = Path(path)
    return parse_bytes(path.name, path.read_bytes(), as_of_date=as_of_date)


def _record_from_chunks(filename: str, content: bytes, chunks: list[EvidenceChunk]) -> EvidenceSourceRecord:
    source_hash = hashlib.sha256(content).hexdigest()
    suffix = Path(filename).suffix.lower()
    if not chunks:
        return EvidenceSourceRecord(
            source_name=filename,
            source_hash=source_hash,
            size_bytes=len(content),
            source_extension=suffix,
            parse_status="parsed_no_text",
            chunk_count=0,
            character_count=0,
            evidence_type=EvidenceType.UNKNOWN,
            evidence_type_tags=[],
            evidence_type_reason="No readable text was extracted from this source.",
            freshness_status=FreshnessStatus.UNKNOWN,
            quality_flags=["no_readable_text"],
            injection_flag=False,
        )

    first = chunks[0]
    return EvidenceSourceRecord(
        source_name=filename,
        source_hash=source_hash,
        size_bytes=len(content),
        source_extension=suffix,
        parse_status="parsed",
        chunk_count=len(chunks),
        character_count=sum(len(chunk.text) for chunk in chunks),
        evidence_type=first.evidence_type,
        evidence_type_tags=list(first.evidence_type_tags),
        evidence_type_reason=first.evidence_type_reason,
        document_date=first.document_date,
        date_source=first.date_source,
        age_days=first.age_days,
        freshness_status=first.freshness_status,
        quality_flags=sorted({flag for chunk in chunks for flag in chunk.quality_flags}),
        injection_flag=any(chunk.injection_flag for chunk in chunks),
    )


def parse_bytes_with_source_record(
    filename: str,
    content: bytes,
    *,
    as_of_date: date | None = None,
) -> tuple[list[EvidenceChunk], EvidenceSourceRecord]:
    """Parse evidence while always returning a document-level provenance record."""

    try:
        chunks = parse_bytes(filename, content, as_of_date=as_of_date)
        return chunks, _record_from_chunks(filename, content, chunks)
    except Exception as exc:
        record = EvidenceSourceRecord(
            source_name=filename,
            source_hash=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
            source_extension=Path(filename).suffix.lower(),
            parse_status="parse_error",
            chunk_count=0,
            character_count=0,
            evidence_type=EvidenceType.UNKNOWN,
            evidence_type_tags=[],
            evidence_type_reason="The source could not be parsed.",
            freshness_status=FreshnessStatus.UNKNOWN,
            quality_flags=["parse_error"],
            injection_flag=False,
            parse_error=f"{type(exc).__name__}: {exc}",
        )
        return [], record


def parse_path_with_source_record(
    path: str | Path,
    *,
    as_of_date: date | None = None,
) -> tuple[list[EvidenceChunk], EvidenceSourceRecord]:
    path = Path(path)
    return parse_bytes_with_source_record(path.name, path.read_bytes(), as_of_date=as_of_date)
