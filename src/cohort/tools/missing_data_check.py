"""Read-only tool: which evidence categories are absent for this patient.

Exists so the case brief can state "what would change the answer" honestly
— a patient with zero recorded labs is not the same as a patient whose labs
are all normal, and an evidence agent that never checks for absence has no
way to tell the two apart.
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from cohort.store.cohort_store import CohortStore

TOOL_NAME = "missing_data_check"


class MissingDataCheckArgs(BaseModel):
    patient_id: str = Field(description="The patient's de-identified id")


def build_missing_data_check_tool(store: CohortStore) -> StructuredTool:
    def missing_data_check(patient_id: str) -> dict[str, object]:
        missing = []
        if not store.get_recent_encounters(patient_id, limit=1):
            missing.append("encounters")
        if not store.get_recent_labs(patient_id, limit=1):
            missing.append("labs")
        if not store.get_medications(patient_id):
            missing.append("medications")
        if not store.get_conditions(patient_id):
            missing.append("conditions")
        return {"missing_data_types": missing}

    return StructuredTool.from_function(
        func=missing_data_check,
        name=TOOL_NAME,
        description=(
            "Returns which evidence categories (encounters, labs, medications, "
            "conditions) have no recorded data for this patient at all."
        ),
        args_schema=MissingDataCheckArgs,
    )
