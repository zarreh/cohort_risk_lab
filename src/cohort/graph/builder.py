from pathlib import Path

import pandas as pd
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from cohort.graph.agents.evidence_agent import build_evidence_agent
from cohort.graph.chains.brief_writer import build_brief_writer_chain
from cohort.graph.edges import route_after_assemble_evidence, route_after_verify
from cohort.graph.nodes.assemble_evidence import build_assemble_evidence_node
from cohort.graph.nodes.await_decision import await_decision_node
from cohort.graph.nodes.done import done_node
from cohort.graph.nodes.draft_brief import build_draft_brief_node
from cohort.graph.nodes.echo import echo_node
from cohort.graph.nodes.load_case import build_load_case_node
from cohort.graph.nodes.record_decision import record_decision_node
from cohort.graph.nodes.verify_brief import verify_brief_node
from cohort.graph.policies import build_fast_model, build_reasoning_model
from cohort.graph.state import CaseReviewState, SkeletonState
from cohort.prompts.loader import load_prompt
from cohort.settings import Settings
from cohort.store.cohort_store import CohortStore
from cohort.tools.registry import build_tools

SkeletonGraph = CompiledStateGraph[SkeletonState, None, SkeletonState, SkeletonState]
CaseReviewGraph = CompiledStateGraph[CaseReviewState, None, CaseReviewState, CaseReviewState]


def build_skeleton_graph() -> SkeletonGraph:
    """The only function that wires nodes and edges. Phase 0: echo -> done."""
    workflow = StateGraph(SkeletonState)
    workflow.add_node("echo", echo_node)
    workflow.add_node("done", done_node)
    workflow.set_entry_point("echo")
    workflow.add_edge("echo", "done")
    workflow.add_edge("done", END)
    return workflow.compile()


def build_case_review_graph(
    settings: Settings,
    model_version_dir: Path,
    feature_table: pd.DataFrame,
    store: CohortStore,
) -> CaseReviewGraph:
    """The only function that wires the case-review graph's nodes and
    edges.

    ```
    load_case -> assemble_evidence <-> tools -> draft_brief
              -> verify_brief --(needs revision)--> assemble_evidence
              -> await_decision [interrupt()] -> record_decision
    ```

    `load_case` sets `risk_score`/`risk_tier` from the deployed model
    directly — no node downstream of it can write to those fields, which
    is D-A12-1 enforced by the state shape itself, not by convention.
    """
    tools = build_tools(store, model_version_dir, feature_table)
    fast_model = build_fast_model(settings)
    reasoning_model = build_reasoning_model(settings)

    evidence_agent = build_evidence_agent(reasoning_model, tools)
    brief_writer = build_brief_writer_chain(fast_model)

    workflow = StateGraph(CaseReviewState)
    # mypy cannot resolve add_node's overloads against a factory-returned
    # Callable (vs. a plain top-level function) — confirmed upstream limitation
    # (same one hit in A2's builder.py), not a real type error; each node is
    # unit-tested directly in tests/graph/.
    workflow.add_node(
        "load_case",
        build_load_case_node(model_version_dir, feature_table),  # type: ignore[arg-type]
    )
    workflow.add_node(
        "assemble_evidence",
        build_assemble_evidence_node(  # type: ignore[arg-type]
            evidence_agent, load_prompt("evidence_agent_v1")
        ),
    )
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node(
        "draft_brief",
        build_draft_brief_node(brief_writer),  # type: ignore[arg-type]
    )
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
