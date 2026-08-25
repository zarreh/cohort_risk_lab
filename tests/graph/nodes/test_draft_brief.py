from cohort.graph.nodes.draft_brief import build_draft_brief_node
from cohort.graph.state import create_initial_case_review_state
from cohort.schemas.case_brief import CaseBrief


class _FakeBriefWriter:
    def __init__(self, brief: CaseBrief) -> None:
        self._brief = brief
        self.last_input: dict[str, object] | None = None

    def invoke(self, input: dict[str, object]) -> CaseBrief:
        self.last_input = input
        return self._brief


def _brief() -> CaseBrief:
    return CaseBrief(
        patient_id="p1",
        narrative="Evidence shows elevated glucose readings.",
        drivers=[],
        corroborating_evidence=[],
        care_gaps=[],
        missing_data=[],
        what_would_change_this="A recent A1c result.",
    )


def test_draft_brief_node_sets_draft_brief_from_chain_output() -> None:
    fake_writer = _FakeBriefWriter(_brief())
    node = build_draft_brief_node(fake_writer)

    state = create_initial_case_review_state("p1")
    result = node(state)

    assert result["draft_brief"] == _brief()


def test_draft_brief_node_passes_messages_to_the_chain() -> None:
    fake_writer = _FakeBriefWriter(_brief())
    node = build_draft_brief_node(fake_writer)

    state = create_initial_case_review_state("p1")
    node(state)

    assert fake_writer.last_input is not None
    assert "messages" in fake_writer.last_input
