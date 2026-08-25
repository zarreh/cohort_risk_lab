"""Terminal node: the decision + override log entry point.

Persistence (Phase 7) writes this to the decision log store; this node's
job in the graph is only to make sure `decision` is present before the
graph reports done — the human, not this node, is the one who decided.
"""

from __future__ import annotations

from cohort.graph.state import CaseReviewState


def record_decision_node(state: CaseReviewState) -> dict[str, object]:
    assert state["decision"] is not None, "record_decision reached with no decision set"
    return {}
