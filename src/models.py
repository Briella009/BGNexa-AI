from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessmentStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIAL = "partially_supported"
    NOT_EVIDENCED = "not_evidenced"
    REVIEW_REQUIRED = "review_required"
    NOT_APPLICABLE = "not_applicable"


class FrameworkSource(BaseModel):
    authority: str
    title: str
    version: str
    source_url: str
    last_verified: str
    source_type: str = "official"
    notes: str | None = None


class Control(BaseModel):
    control_id: str
    reference: str
    title: str
    requirement_summary: str
    evidence_examples: list[str] = Field(default_factory=list)
    capability_tags: list[str] = Field(default_factory=list)
    weight: float = 1.0
    source_locator: str
    verification_status: str
    applicability: dict[str, Any] = Field(default_factory=dict)
    source_pdf_pages: list[int] = Field(default_factory=list)
    verification_note: str | None = None
    notes: str | None = None


class Framework(BaseModel):
    framework_id: str
    name: str
    jurisdiction: str
    version: str
    authority: str
    source: FrameworkSource
    scope_note: str
    copyright_mode: str = "public_source"
    framework_type: str = "framework"
    controls: list[Control]


class EvidenceChunk(BaseModel):
    chunk_id: str
    source_name: str
    text: str
    page: int | None = None
    injection_flag: bool = False
    content_hash: str | None = None


class EvidenceMatch(BaseModel):
    chunk_id: str
    source_name: str
    excerpt: str
    retrieval_score: float
    page: int | None = None
    injection_flag: bool = False
    content_hash: str | None = None
    lexical_score: float | None = None
    semantic_score: float | None = None
    retrieval_method: str = "tfidf"


class AssessmentResult(BaseModel):
    control_id: str
    framework_id: str
    status: AssessmentStatus
    rationale: str
    evidence: list[EvidenceMatch] = Field(default_factory=list)
    recommendation: str | None = None
    evidence_strength: str = "none"
    ai_assessed: bool = False
    requires_human_review: bool = True
    human_validated: bool = False
    reviewer: str | None = None
    reviewer_note: str | None = None
    reviewed_at: str | None = None


class HumanValidation(BaseModel):
    control_id: str
    framework_id: str
    original_status: AssessmentStatus
    validated_status: Literal["supported", "partially_supported", "not_evidenced", "review_required"]
    reviewer: str
    note: str
    evidence_confirmed: bool = False
    reviewed_at: str


class CopilotCitation(BaseModel):
    citation_type: Literal["evidence", "framework"]
    citation_id: str
    label: str
    locator: str | None = None


class CopilotAnswer(BaseModel):
    answer: str
    confidence: Literal["high", "medium", "low"] = "low"
    evidence_citations: list[CopilotCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    ai_generated: bool = False
    blocked_reason: str | None = None


class ScoreSummary(BaseModel):
    provisional_readiness_percent: float | None
    resolved_weight: float
    applicable_weight: float
    coverage_percent: float
    supported: int
    partial: int
    not_evidenced: int
    review_required: int
    not_applicable: int
