from cohort.graph.nodes.verify_brief import brief_needs_revision, verify_brief_node
from cohort.graph.state import MAX_REVISIONS, create_initial_case_review_state
from cohort.schemas.case_brief import CaseBrief


def _state_with_brief(narrative: str, revision_count: int = 0) -> dict[str, object]:
    state = create_initial_case_review_state("p1")
    state["draft_brief"] = CaseBrief(
        patient_id="p1",
        narrative=narrative,
        drivers=[],
        corroborating_evidence=[],
        care_gaps=[],
        missing_data=[],
        what_would_change_this="More labs would help.",
    )
    state["revision_count"] = revision_count
    return state  # type: ignore[return-value]


def test_clean_brief_produces_no_feedback_messages() -> None:
    state = _state_with_brief("The evidence shows elevated glucose and two active conditions.")
    result = verify_brief_node(state)  # type: ignore[arg-type]
    assert result["verification_feedback"] == []
    assert "messages" not in result


def test_decision_language_produces_feedback_message() -> None:
    state = _state_with_brief("We recommend enrolling this patient immediately.")
    result = verify_brief_node(state)  # type: ignore[arg-type]
    assert result["verification_feedback"] != []
    assert "messages" in result


def test_revision_count_increments_every_call() -> None:
    state = _state_with_brief("Clean evidence summary.", revision_count=1)
    result = verify_brief_node(state)  # type: ignore[arg-type]
    assert result["revision_count"] == 2


def test_needs_revision_true_when_violations_and_under_max() -> None:
    state = _state_with_brief("We recommend enrollment.", revision_count=0)
    state.update(verify_brief_node(state))  # type: ignore[arg-type]
    assert brief_needs_revision(state)  # type: ignore[arg-type]


def test_needs_revision_false_once_max_revisions_reached() -> None:
    state = _state_with_brief("We recommend enrollment.", revision_count=MAX_REVISIONS)
    state.update(verify_brief_node(state))  # type: ignore[arg-type]
    assert not brief_needs_revision(state)  # type: ignore[arg-type]


def test_needs_revision_false_when_clean() -> None:
    state = _state_with_brief("Clean evidence summary with no decision language.")
    state.update(verify_brief_node(state))  # type: ignore[arg-type]
    assert not brief_needs_revision(state)  # type: ignore[arg-type]
