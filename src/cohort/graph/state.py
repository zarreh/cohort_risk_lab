from collections.abc import Sequence
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from cohort.schemas.case_brief import CaseBrief, Driver


class SkeletonState(TypedDict):
    """Phase 0 walking-skeleton state — kept as the template's trivial proof graph."""

    message: str
    echoed: str
    done: bool


def create_initial_skeleton_state(message: str) -> SkeletonState:
    return SkeletonState(message=message, echoed="", done=False)


MAX_REVISIONS = 2

Decision = Literal["enrol", "decline", "defer"]


class CaseReviewState(TypedDict):
    """State for the case-review graph (docs/PLAN.md §Phases, Phase 6).

    `risk_tier` and `risk_score` are set once, in `nodes/load_case.py`,
    directly from the deployed model's own prediction — never touched by
    any LLM node in this graph. This is D-A12-1's structural enforcement at
    the state-shape level: there is no field an agent node could write a
    tier or a decision into, mirroring `CaseBrief`'s own missing fields.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    patient_id: str
    risk_score: float
    risk_tier: str
    drivers: list[Driver]
    draft_brief: CaseBrief | None
    verification_feedback: list[str]
    revision_count: int
    decision: Decision | None
    override_notes: str | None


def create_initial_case_review_state(patient_id: str) -> CaseReviewState:
    """The only place default field values are decided — never scattered
    across nodes."""
    return CaseReviewState(
        messages=[],
        patient_id=patient_id,
        risk_score=0.0,
        risk_tier="",
        drivers=[],
        draft_brief=None,
        verification_feedback=[],
        revision_count=0,
        decision=None,
        override_notes=None,
    )
