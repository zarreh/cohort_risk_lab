"""Checks the drafted brief for decision language before it ever reaches a
clinician — the grounding-loop pattern from A2's `judge_grounding.py`,
adapted: the check here is deterministic (`no_decision_guard`), not a
second LLM call, because "does this text contain a decision verb" doesn't
need judgement to answer.

On a violation, folds specific feedback back into the conversation as a
`HumanMessage` so the next `draft_brief` pass targets the exact problem,
the same feedback-loop shape `judge_grounding.py` uses.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from cohort.graph.state import MAX_REVISIONS, CaseReviewState
from cohort.guardrails.no_decision_guard import find_decision_language


def _feedback_text(violations: list[str]) -> str:
    header = (
        "The drafted brief contains decision or recommendation language, "
        "which is not permitted. Rewrite it to describe only the evidence:"
    )
    return header + "\n" + "\n".join(f"- {v}" for v in violations)


def verify_brief_node(state: CaseReviewState) -> dict[str, object]:
    brief = state["draft_brief"]
    assert brief is not None

    violations = find_decision_language(brief)
    delta: dict[str, object] = {
        "verification_feedback": violations,
        "revision_count": state["revision_count"] + 1,
    }
    if violations:
        delta["messages"] = [HumanMessage(content=_feedback_text(violations))]
    return delta


def brief_needs_revision(state: CaseReviewState) -> bool:
    return bool(state["verification_feedback"]) and state["revision_count"] < MAX_REVISIONS
