"""Exercises the interrupt()/resume cycle end to end, isolated from the
LLM-dependent nodes: `await_decision` and `record_decision` are the only
two nodes in this graph, wired through a real checkpointer, so the
interrupt/resume glue is verified against the real langgraph runtime
rather than assumed to work.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from cohort.graph.nodes.await_decision import await_decision_node
from cohort.graph.nodes.record_decision import record_decision_node
from cohort.graph.state import CaseReviewState, create_initial_case_review_state
from cohort.schemas.case_brief import CaseBrief


def _hitl_only_graph() -> CompiledStateGraph[
    CaseReviewState, None, CaseReviewState, CaseReviewState
]:
    workflow = StateGraph(CaseReviewState)
    workflow.add_node("await_decision", await_decision_node)
    workflow.add_node("record_decision", record_decision_node)
    workflow.set_entry_point("await_decision")
    workflow.add_edge("await_decision", "record_decision")
    workflow.add_edge("record_decision", END)
    return workflow.compile(checkpointer=MemorySaver())


def _initial_state() -> CaseReviewState:
    state = create_initial_case_review_state("p1")
    state["risk_tier"] = "high"
    state["risk_score"] = 0.9
    state["draft_brief"] = CaseBrief(
        patient_id="p1",
        narrative="Evidence summary.",
        drivers=[],
        corroborating_evidence=[],
        care_gaps=[],
        missing_data=[],
        what_would_change_this="More labs.",
    )
    return state


def test_graph_pauses_with_the_review_request_payload() -> None:
    graph = _hitl_only_graph()
    config = RunnableConfig(configurable={"thread_id": "t1"})

    result = graph.invoke(_initial_state(), config=config)

    assert "__interrupt__" in result
    payload = result["__interrupt__"][0].value
    assert payload["patient_id"] == "p1"
    assert payload["risk_tier"] == "high"


def test_resuming_with_a_decision_completes_the_graph() -> None:
    graph = _hitl_only_graph()
    config = RunnableConfig(configurable={"thread_id": "t2"})

    graph.invoke(_initial_state(), config=config)
    final_state = graph.invoke(
        Command(resume={"decision": "enrol", "notes": "Confirmed with clinician."}),
        config=config,
    )

    assert final_state["decision"] == "enrol"
    assert final_state["override_notes"] == "Confirmed with clinician."


def test_record_decision_asserts_when_reached_without_a_decision() -> None:
    state = _initial_state()
    try:
        record_decision_node(state)
        raised = False
    except AssertionError:
        raised = True
    assert raised
