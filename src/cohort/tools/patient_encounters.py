"""Read-only tool: a patient's recent encounters. The evidence agent uses
this to corroborate (or fail to corroborate) the case brief's drivers.
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from cohort.guardrails.phi_projection import project
from cohort.store.cohort_store import CohortStore

TOOL_NAME = "patient_encounters"


class PatientEncountersArgs(BaseModel):
    patient_id: str = Field(description="The patient's de-identified id")
    limit: int = Field(default=10, description="Maximum encounters to return, most recent first")


def build_patient_encounters_tool(store: CohortStore) -> StructuredTool:
    def patient_encounters(patient_id: str, limit: int = 10) -> list[dict[str, object]]:
        encounters = store.get_recent_encounters(patient_id, limit=limit)
        return [project(e, TOOL_NAME) for e in encounters]

    return StructuredTool.from_function(
        func=patient_encounters,
        name=TOOL_NAME,
        description=(
            "Returns a patient's most recent encounters (date, care setting, "
            "reason) — read-only, no cost or billing fields."
        ),
        args_schema=PatientEncountersArgs,
    )
