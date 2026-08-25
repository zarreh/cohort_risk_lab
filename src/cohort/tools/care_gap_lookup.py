"""Read-only tool: common preventive-care gaps given a patient's known
chronic conditions — e.g. a diabetic patient with no recent A1c/glucose
lab, or a hypertensive patient with no recent blood-pressure reading.

Deliberately simple, explicit rules rather than a model: a care gap is a
concrete, auditable clinical fact ("no glucose test recorded since 2023"),
not a prediction, and the evidence agent needs to be able to say exactly
why it flagged one.
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from cohort.store.cohort_store import CohortStore

TOOL_NAME = "care_gap_lookup"

# condition keyword -> (expected lab/vital keyword, gap description)
CARE_GAP_RULES: dict[str, tuple[str, str]] = {
    "diabetes": ("glucose", "No glucose or A1c lab recorded for a patient with diabetes"),
    "hypertension": (
        "blood pressure",
        "No blood pressure reading recorded for a patient with hypertension",
    ),
}


class CareGapLookupArgs(BaseModel):
    patient_id: str = Field(description="The patient's de-identified id")


def build_care_gap_lookup_tool(store: CohortStore) -> StructuredTool:
    def care_gap_lookup(patient_id: str) -> list[dict[str, object]]:
        conditions = {
            c.description.lower() for c in store.get_conditions(patient_id) if c.is_active
        }
        labs = store.get_recent_labs(patient_id, limit=200)
        lab_descriptions = {lab.description.lower() for lab in labs}

        gaps: list[dict[str, object]] = []
        for condition_keyword, (lab_keyword, description) in CARE_GAP_RULES.items():
            has_condition = any(condition_keyword in c for c in conditions)
            has_expected_lab = any(lab_keyword in d for d in lab_descriptions)
            if has_condition and not has_expected_lab:
                gaps.append({"gap_description": description, "last_relevant_encounter": None})

        return gaps

    return StructuredTool.from_function(
        func=care_gap_lookup,
        name=TOOL_NAME,
        description=(
            "Checks for common preventive-care gaps given the patient's known chronic conditions."
        ),
        args_schema=CareGapLookupArgs,
    )
