from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Status(StrEnum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class RiskCase(BaseModel):
    id: str = Field(..., description="Unique risk case ID, e.g. RC-001")
    title: str
    description: str
    category: str
    severity: str
    owner: str
    mitigation: str
    impact: str | None = None
    likelihood: str | None = None
    affected_assets: list[str] | None = Field(default_factory=list)
    reported_date: str | None = None
    detection_method: str | None = None
    tags: list[str] | None = Field(default_factory=list)
    raw: dict[str, Any] | None = None


class MissingField(BaseModel):
    field: str
    reason: str


class CompletenessReport(BaseModel):
    is_complete: bool
    missing: list[MissingField] = Field(default_factory=list)
    completeness_score: int = Field(ge=0, le=100)
    notes: list[str] = Field(default_factory=list)


class SimilarCase(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    outcome: str
    reasoning: str
    score: float = Field(ge=0.0, le=1.0)


class DecisionPackage(BaseModel):
    package_id: str
    risk_case_id: str
    summary: str
    completeness_report: CompletenessReport
    missing_information: list[str] = Field(default_factory=list)
    similar_cases: list[SimilarCase] = Field(default_factory=list)
    questions_for_experts: list[str] = Field(default_factory=list)
    status: Status = Status.draft
    reviewer_name: str | None = None
    reviewed_at: datetime | None = None
    approval_reason: str | None = None


class ApprovalRecord(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    package_id: str
    risk_case_id: str | None = None
    reviewer_name: str
    action: Literal["approve", "reject"]
    reason: str | None = None
