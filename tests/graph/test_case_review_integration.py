"""Integration test: wires the real graph (real nodes, real edges, real
tools against the fixture DB, a real trained sklearn model) with fake
LLM-backed pieces (evidence agent, brief writer), proving the graph's
control flow — including a genuine interrupt()/resume cycle — end to end
without ever calling a live model. Same approach as A2's
`test_surveillance_graph_integration.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage, ToolCall
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from cohort.graph.edges import route_after_assemble_evidence, route_after_verify
from cohort.graph.nodes.assemble_evidence import build_assemble_evidence_node
from cohort.graph.nodes.await_decision import await_decision_node
from cohort.graph.nodes.draft_brief import build_draft_brief_node
from cohort.graph.nodes.load_case import build_load_case_node
from cohort.graph.nodes.record_decision import record_decision_node
from cohort.graph.nodes.verify_brief import verify_brief_node
from cohort.graph.state import CaseReviewState
from cohort.pipeline.features.extract import BINARY_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import ModelMetadata, save_model_artifact
from cohort.schemas.case_brief import CaseBrief
from cohort.store.cohort_store import CohortStore
from cohort.tools.registry import build_tools
from tests.fixtures.cohort_db import build_test_cohort_db

N = 60


class _FakeEvidenceAgent:
    """First call: requests one tool call. Second call: declares done."""

    def __init__(self) -> None:
        self._calls = 0

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        self._calls += 1
        if self._calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    ToolCall(name="patient_encounters", args={"patient_id": "p1"}, id="call-1")
                ],
            )
        return AIMessage(content="I have gathered sufficient evidence.")


class _FakeBriefWriter:
    def invoke(self, input: dict[str, object]) -> CaseBrief:
        return CaseBrief(
            patient_id="p1",
            narrative="Elevated risk score with corroborating encounter history.",
            drivers=[],
            corroborating_evidence=[],
            care_gaps=[],
            missing_data=[],
            what_would_change_this="A recent lab result would clarify this further.",
        )


def _synthetic_feature_table() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data: dict[str, object] = {"PATIENT_ID": ["p1"] + [f"bg{i}" for i in range(N - 1)]}
    for col in NUMERIC_FEATURES:
        data[col] = rng.normal(size=N)
    for col in CATEGORICAL_FEATURES:
        data[col] = rng.choice(["A", "B"], size=N)
    for col in BINARY_FEATURES:
        data[col] = rng.choice([True, False], size=N)
    return pd.DataFrame(data)


def _train_and_register(features: pd.DataFrame, tmp_path: Path) -> Path:
    preprocess = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression())])
    x = features[FEATURE_COLUMNS]
    y = (features[NUMERIC_FEATURES[0]] > 0).astype(int)
    pipeline.fit(x, y)
    metadata = ModelMetadata("v_test", "Y_TEST", 0.0, N, 0, {}, FEATURE_COLUMNS)
    return save_model_artifact(pipeline, metadata, tmp_path)


def _build_test_graph(model_version_dir: Path, feature_table: pd.DataFrame, store: CohortStore):  # type: ignore[no-untyped-def]
    tools = build_tools(store, model_version_dir, feature_table)
    evidence_agent = _FakeEvidenceAgent()
    brief_writer = _FakeBriefWriter()

    workflow = StateGraph(CaseReviewState)
    workflow.add_node(
        "load_case",
        build_load_case_node(model_version_dir, feature_table),  # type: ignore[arg-type]
    )
    workflow.add_node(
        "assemble_evidence",
        build_assemble_evidence_node(evidence_agent, "system prompt"),  # type: ignore[arg-type]
    )
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("draft_brief", build_draft_brief_node(brief_writer))  # type: ignore[arg-type]
    workflow.add_node("verify_brief", verify_brief_node)
    workflow.add_node("await_decision", await_decision_node)
    workflow.add_node("record_decision", record_decision_node)

    workflow.set_entry_point("load_case")
    workflow.add_edge("load_case", "assemble_evidence")
    workflow.add_conditional_edges("assemble_evidence", route_after_assemble_evidence)
    workflow.add_edge("tools", "assemble_evidence")
    workflow.add_edge("draft_brief", "verify_brief")
    workflow.add_conditional_edges("verify_brief", route_after_verify)
    workflow.add_edge("await_decision", "record_decision")
    workflow.add_edge("record_decision", END)

    return workflow.compile(checkpointer=MemorySaver())


def test_full_case_review_reaches_await_decision_and_resumes(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    version_dir = _train_and_register(features, tmp_path)

    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    store = CohortStore(db_path)

    graph = _build_test_graph(version_dir, features, store)
    config = RunnableConfig(configurable={"thread_id": str(uuid4())})

    result = graph.invoke(
        {
            "messages": [],
            "patient_id": "p1",
            "risk_score": 0.0,
            "risk_tier": "",
            "drivers": [],
            "draft_brief": None,
            "verification_feedback": [],
            "revision_count": 0,
            "decision": None,
            "override_notes": None,
        },
        config=config,
    )

    # Reached the HITL pause with a clean brief already drafted.
    assert "__interrupt__" in result
    payload = result["__interrupt__"][0].value
    assert payload["patient_id"] == "p1"
    assert "risk_score" in payload

    final_state = graph.invoke(
        Command(resume={"decision": "defer", "notes": "Needs another lab result."}),
        config=config,
    )

    assert final_state["decision"] == "defer"
    assert final_state["override_notes"] == "Needs another lab result."
    assert final_state["draft_brief"] is not None
    # Proves the evidence agent's tool call actually ran against the real store.
    tool_messages = [m for m in final_state["messages"] if getattr(m, "type", None) == "tool"]
    assert len(tool_messages) == 1
