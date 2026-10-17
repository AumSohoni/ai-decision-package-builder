from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone
from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


class Status(str, Enum):
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
    impact: Optional[str] = None
    likelihood: Optional[str] = None
    affected_assets: Optional[List[str]] = Field(default_factory=list)
    reported_date: Optional[str] = None
    detection_method: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None


class MissingField(BaseModel):
    field: str
    reason: str


class CompletenessReport(BaseModel):
    is_complete: bool
    missing: List[MissingField] = Field(default_factory=list)
    completeness_score: int = Field(ge=0, le=100)
    notes: List[str] = Field(default_factory=list)


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
    missing_information: List[str] = Field(default_factory=list)
    similar_cases: List[SimilarCase] = Field(default_factory=list)
    questions_for_experts: List[str] = Field(default_factory=list)
    status: Status = Status.draft
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approval_reason: Optional[str] = None


class ApprovalRecord(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    package_id: str
    risk_case_id: Optional[str] = None
    reviewer_name: str
    action: Literal["approve", "reject"]
    reason: Optional[str] = None
