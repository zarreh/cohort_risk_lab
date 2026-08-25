"""Suspends the graph for a human decision — the HITL pattern from the
source `healthcare_hitl_assistant.ipynb`, kept because it is the one part
of that notebook worth keeping (docs/PLAN.md §3 "what survives").

`interrupt()` pauses execution and persists state to the checkpointer;
the caller resumes with `Command(resume={"decision": ..., "notes": ...})`.
This node never decides anything itself — it only packages what a
clinician needs to see and waits.
"""

from __future__ import annotations

from langgraph.types import interrupt

from cohort.graph.state import CaseReviewState


def await_decision_node(state: CaseReviewState) -> dict[str, object]:
    brief = state["draft_brief"]
    assert brief is not None

    review_request = {
        "patient_id": state["patient_id"],
        "risk_score": state["risk_score"],
        "risk_tier": state["risk_tier"],
        "brief": brief.model_dump(),
        "instructions": "Respond with decision: 'enrol' | 'decline' | 'defer', and optional notes.",
    }
    response = interrupt(review_request)
    return {
        "decision": response["decision"],
        "override_notes": response.get("notes"),
    }
