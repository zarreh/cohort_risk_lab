"""Structural test: the case-review graph compiles with the exact node
set and shape the plan calls for, and each ChatOpenAI construction only
needs *a* key string, never a valid one — this test never calls the API."""

from collections.abc import Generator
from pathlib import Path

import pandas as pd
import pytest

from cohort.graph.builder import build_case_review_graph
from cohort.settings import get_settings
from cohort.store.cohort_store import CohortStore
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("COHORT_OPENAI_API_KEY", "sk-fake-key-for-construction-only")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_graph_compiles_with_the_expected_nodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    from cohort.pipeline.registry import ModelMetadata, save_model_artifact

    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    store = CohortStore(db_path)

    features = pd.DataFrame({"PATIENT_ID": ["p1", "p2"], "AGE_AT_INDEX": [40.0, 60.0]})
    pipeline = Pipeline(steps=[("model", LogisticRegression())])
    pipeline.fit([[40.0], [60.0]], [0, 1])
    metadata = ModelMetadata("v_test", "Y_TEST", 0.5, 2, 0, {}, ["AGE_AT_INDEX"])
    version_dir = save_model_artifact(pipeline, metadata, tmp_path)

    graph = build_case_review_graph(get_settings(), version_dir, features, store)

    node_names = set(graph.get_graph().nodes.keys()) - {"__start__", "__end__"}
    assert node_names == {
        "load_case",
        "assemble_evidence",
        "tools",
        "draft_brief",
        "verify_brief",
        "await_decision",
        "record_decision",
    }
