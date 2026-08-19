from __future__ import annotations

import hashlib
import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .models import EvidenceChunk
from .security import contains_prompt_injection


def _chunk_text(text: str, source_name: str, page: int | None = None, size: int = 1200, overlap: int = 180) -> list[EvidenceChunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

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
            )
        )
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
        index += 1
    return chunks


def parse_bytes(filename: str, content: bytes) -> list[EvidenceChunk]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        chunks: list[EvidenceChunk] = []
        for i, page in enumerate(reader.pages, start=1):
            chunks.extend(_chunk_text(page.extract_text() or "", filename, page=i))
        return chunks

    if suffix == ".docx":
        document = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in document.paragraphs)
        return _chunk_text(text, filename)

    if suffix in {".txt", ".md"}:
        return _chunk_text(content.decode("utf-8", errors="ignore"), filename)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def parse_path(path: str | Path) -> list[EvidenceChunk]:
    path = Path(path)
    return parse_bytes(path.name, path.read_bytes())
