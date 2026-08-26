"""API-contract request/response models — separate from `schemas/`, which
holds the domain models the graph itself produces.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueueEntryResponse(BaseModel):
    patient_id: str
    risk_score: float
    risk_tier: str
    status: str
    created_at: str
    updated_at: str


class StartReviewResponse(BaseModel):
    patient_id: str
    status: str


class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(enrol|decline|defer)$")
    notes: str | None = Field(default=None, max_length=2000)


class CaseDetailResponse(BaseModel):
    patient_id: str
    risk_score: float
    risk_tier: str
    status: str
    decision: str | None
    override_notes: str | None
    decided_at: str | None


class SubgroupAuditRow(BaseModel):
    stratum: str
    n: int
    sufficient_n: bool
    calibration_in_the_large: float | None
    expected_calibration_error: float | None
    tpr: float | None
    tpr_ci_lower: float | None
    tpr_ci_upper: float | None
    enrolment_rate: float | None
    enrolment_rate_ci_lower: float | None
    enrolment_rate_ci_upper: float | None


class LabelChoiceRow(BaseModel):
    race: str
    n: int
    burden_enrolment_rate: float
    cost_enrolment_rate: float
    gap_percentage_points: float
