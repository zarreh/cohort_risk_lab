"""Drafts the case brief from the evidence conversation. Runs after
`assemble_evidence` has gathered whatever it could — this node only
synthesises, it does not call tools itself.
"""

from __future__ import annotations

from collections.abc import Callable

from cohort.graph.protocols import BriefWriterChain
from cohort.graph.state import CaseReviewState


def build_draft_brief_node(
    brief_writer: BriefWriterChain,
) -> Callable[[CaseReviewState], dict[str, object]]:
    def draft_brief_node(state: CaseReviewState) -> dict[str, object]:
        brief = brief_writer.invoke({"messages": state["messages"]})
        return {"draft_brief": brief}

    return draft_brief_node
