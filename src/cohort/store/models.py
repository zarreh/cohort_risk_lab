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
