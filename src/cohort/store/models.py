"""Typed records returned by `CohortStore`. Every field here has already
passed through `data/deidentify.py` — no direct identifier ever reaches
this layer, let alone a tool or the agent above it.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PatientRecord(BaseModel):
    patient_id: str
    race: str
    ethnicity: str
    gender: str
    marital: str | None
    income: float


class Condition(BaseModel):
    patient_id: str
    start: datetime
    stop: datetime | None
    description: str

    @property
    def is_active(self) -> bool:
        return self.stop is None


class Encounter(BaseModel):
    patient_id: str
    start: datetime
    stop: datetime | None
    encounter_class: str
    description: str
    total_claim_cost: float


class Medication(BaseModel):
    patient_id: str
    start: datetime
    stop: datetime | None
    description: str


class LabObservation(BaseModel):
    patient_id: str
    date: datetime
    category: str
    description: str
    value: str
    units: str | None


class ReviewCase(BaseModel):
    """One row in the review queue — the operational record of a patient's
    case review, from being flagged through to a clinician's decision."""

    patient_id: str
    risk_score: float
    risk_tier: str
    status: str  # "pending" | "in_review" | "awaiting_decision" | "decided"
    created_at: str
    updated_at: str
    decision: str | None
    override_notes: str | None
    decided_at: str | None


class ReviewEvent(BaseModel):
    """One node-execution event in a case review, persisted so a run is
    replayable from the store at any time — during execution or long after
    it finished."""

    patient_id: str
    sequence: int
    node: str
    payload_json: str
    created_at: str
