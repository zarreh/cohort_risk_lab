"""The case brief: what the evidence agent produces, and — by what it
cannot contain — the structural enforcement of D-A12-1 ("the LLM is not
the risk model").

There is no risk-tier field and no enrolment/recommendation field anywhere
in this schema. The risk tier is set once, upstream, by the trained model
(`graph/nodes/load_case.py`) and flows into `CaseReviewState` directly —
never through anything an LLM writes. A brief-writing chain that wanted to
sneak a decision in would have nowhere in the *structure* to put it; the
only place a decision could hide is prose, which is exactly what
`guardrails/no_decision_guard.py` checks.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Driver(BaseModel):
    """One feature's contribution to the model's own risk score — never
    authored by the LLM, always copied verbatim from the deployed model's
    SHAP output (`pipeline/explain/shap_explainer.py`)."""

    feature_name: str
    contribution: float
    direction: str


class CorroboratingEvidence(BaseModel):
    source: str = Field(description="Which tool this came from, e.g. 'encounter', 'lab'")
    description: str


class CaseBrief(BaseModel):
    """The evidence agent's output. `narrative` is the only free-text field
    an LLM authors — everything else is either copied from tool output or
    a plain list of strings the writer chain selects from evidence already
    gathered, not invents."""

    patient_id: str
    narrative: str = Field(
        description=(
            "A short synthesis of the evidence for a clinician, in plain "
            "language. Must describe what the evidence shows — never "
            "recommend, suggest, or state what should happen to the patient."
        )
    )
    drivers: list[Driver]
    corroborating_evidence: list[CorroboratingEvidence]
    care_gaps: list[str]
    missing_data: list[str]
    what_would_change_this: str = Field(
        description="What additional evidence would change this assessment, stated neutrally."
    )
