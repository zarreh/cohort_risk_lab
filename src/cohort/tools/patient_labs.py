"""Read-only tool: a patient's recent lab and vital-sign observations."""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from cohort.guardrails.phi_projection import project
from cohort.store.cohort_store import CohortStore

TOOL_NAME = "patient_labs"


class PatientLabsArgs(BaseModel):
    patient_id: str = Field(description="The patient's de-identified id")
    limit: int = Field(default=10, description="Maximum lab results to return, most recent first")


def build_patient_labs_tool(store: CohortStore) -> StructuredTool:
    def patient_labs(patient_id: str, limit: int = 10) -> list[dict[str, object]]:
        labs = store.get_recent_labs(patient_id, limit=limit)
        return [project(lab, TOOL_NAME) for lab in labs]

    return StructuredTool.from_function(
        func=patient_labs,
        name=TOOL_NAME,
        description="Returns a patient's most recent lab results and vital signs.",
        args_schema=PatientLabsArgs,
    )
