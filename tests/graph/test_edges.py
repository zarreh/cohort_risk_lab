from langchain_core.messages import AIMessage, ToolCall

from cohort.graph.edges import route_after_assemble_evidence, route_after_verify
from cohort.graph.state import MAX_REVISIONS, create_initial_case_review_state


def test_routes_to_tools_when_ai_message_requests_a_tool_call() -> None:
    state = create_initial_case_review_state("p1")
    state["messages"] = [
        AIMessage(
            content="",
            tool_calls=[ToolCall(name="patient_labs", args={"patient_id": "p1"}, id="1")],
        )
    ]
    assert route_after_assemble_evidence(state) == "tools"


def test_routes_to_draft_brief_when_no_tool_call() -> None:
    state = create_initial_case_review_state("p1")
    state["messages"] = [AIMessage(content="I have gathered enough evidence.")]
    assert route_after_assemble_evidence(state) == "draft_brief"


def test_routes_to_assemble_evidence_when_revision_needed() -> None:
    state = create_initial_case_review_state("p1")
    state["verification_feedback"] = ["decision language found"]
    state["revision_count"] = 0
    assert route_after_verify(state) == "assemble_evidence"


def test_routes_to_await_decision_when_clean() -> None:
    state = create_initial_case_review_state("p1")
    state["verification_feedback"] = []
    assert route_after_verify(state) == "await_decision"


def test_routes_to_await_decision_once_max_revisions_reached_even_if_dirty() -> None:
    state = create_initial_case_review_state("p1")
    state["verification_feedback"] = ["decision language found"]
    state["revision_count"] = MAX_REVISIONS
    assert route_after_verify(state) == "await_decision"
