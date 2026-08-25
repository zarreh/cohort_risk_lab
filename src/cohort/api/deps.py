from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import Request

from cohort.graph.builder import (
    CaseReviewGraph,
    SkeletonGraph,
    build_case_review_graph,
    build_skeleton_graph,
)
from cohort.pipeline.models.train import build_scored_feature_table
from cohort.settings import Settings, get_settings
from cohort.store.cohort_store import CohortStore
from cohort.store.queue_store import QueueStore

DEPLOYED_MODEL_VERSION = "v1_burden"


def settings_dependency() -> Settings:
    return get_settings()


@lru_cache
def get_compiled_graph() -> SkeletonGraph:
    """Single compiled-graph instance, shared across requests."""
    return build_skeleton_graph()


@lru_cache
def get_cohort_store() -> CohortStore:
    return CohortStore(Path(get_settings().cohort_db_path))


@lru_cache
def get_queue_store() -> QueueStore:
    return QueueStore(Path(get_settings().queue_store_path))


@lru_cache
def get_feature_table() -> pd.DataFrame:
    """Loaded once per process — extracted, access-gap-adjusted features
    for the whole scored cohort, the identical table
    `pipeline/models/train.py` trained the deployed model against
    (`build_scored_feature_table` is shared between the two so they cannot
    silently drift apart). Rebuilding this per request would recompute
    feature aggregates on every call for no reason: the cohort only
    changes when `make data && make train` reruns, which means a process
    restart, not a request."""
    _patients, features = build_scored_feature_table()
    return features


def get_case_review_graph(request: Request) -> CaseReviewGraph:
    """One compiled graph per process, built lazily on first request and
    cached on `app.state` — not `@lru_cache`, because it needs the
    checkpointer the lifespan handler opened at startup
    (`api/main.py`), which isn't available at import time."""
    if not hasattr(request.app.state, "case_review_graph"):
        request.app.state.case_review_graph = build_case_review_graph(
            get_settings(),
            Path(get_settings().registry_dir) / DEPLOYED_MODEL_VERSION,
            get_feature_table(),
            get_cohort_store(),
            checkpointer=request.app.state.checkpointer,
        )
    graph: CaseReviewGraph = request.app.state.case_review_graph
    return graph
