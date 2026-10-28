"""Entry point for `langgraph dev` (see `langgraph.json` and `make studio`).

Builds the same case-review graph the API runs, from the same deployed
model, feature table and cohort store, but compiled without a checkpointer:
the LangGraph dev server provides its own persistence, including the
`await_decision` interrupt, so Studio can pause and resume a review.
"""

from __future__ import annotations

from pathlib import Path

from cohort.api.deps import DEPLOYED_MODEL_VERSION, get_cohort_store, get_feature_table
from cohort.graph.builder import CaseReviewGraph, build_case_review_workflow
from cohort.settings import get_settings


def make_case_review_graph() -> CaseReviewGraph:
    settings = get_settings()
    workflow = build_case_review_workflow(
        settings,
        Path(settings.registry_dir) / DEPLOYED_MODEL_VERSION,
        get_feature_table(),
        get_cohort_store(),
    )
    return workflow.compile()
