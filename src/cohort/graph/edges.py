"""Routing predicates — one small function each, so `builder.py` stays the
only place that reads like a picture of the whole graph.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage

from cohort.graph.nodes.verify_brief import brief_needs_revision
from cohort.graph.state import CaseReviewState


def route_after_assemble_evidence(state: CaseReviewState) -> Literal["tools", "draft_brief"]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "draft_brief"


def route_after_verify(state: CaseReviewState) -> Literal["assemble_evidence", "await_decision"]:
    if brief_needs_revision(state):
        return "assemble_evidence"
    return "await_decision"
