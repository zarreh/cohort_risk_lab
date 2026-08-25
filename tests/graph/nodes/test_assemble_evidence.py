from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from cohort.graph.nodes.assemble_evidence import build_assemble_evidence_node
from cohort.graph.state import create_initial_case_review_state
from cohort.schemas.case_brief import Driver


class _FakeEvidenceAgent:
    def __init__(self, response: AIMessage) -> None:
        self._response = response
        self.last_conversation: Sequence[BaseMessage] | None = None

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        self.last_conversation = messages
        return self._response


def test_seeds_system_and_human_message_on_first_call() -> None:
    fake_agent = _FakeEvidenceAgent(AIMessage(content="done"))
    node = build_assemble_evidence_node(fake_agent, "You are an evidence assistant.")

    state = create_initial_case_review_state("p1")
    state["risk_tier"] = "high"
    state["risk_score"] = 0.82
    state["drivers"] = [
        Driver(feature_name="AGE_AT_INDEX", contribution=0.1, direction="increases_risk")
    ]

    result = node(state)

    messages = result["messages"]
    assert isinstance(messages, list)
    assert isinstance(messages[0], SystemMessage)
    assert len(messages) == 3  # system, human seed, agent response


def test_does_not_reseed_on_subsequent_calls() -> None:
    fake_agent = _FakeEvidenceAgent(AIMessage(content="more evidence"))
    node = build_assemble_evidence_node(fake_agent, "system prompt")

    state = create_initial_case_review_state("p1")
    state["messages"] = [SystemMessage(content="already seeded"), AIMessage(content="prior turn")]

    result = node(state)

    messages = result["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 1  # only the new agent response, no reseed


def test_driver_context_is_included_in_seed_message() -> None:
    fake_agent = _FakeEvidenceAgent(AIMessage(content="done"))
    node = build_assemble_evidence_node(fake_agent, "system prompt")

    state = create_initial_case_review_state("p1")
    state["drivers"] = [
        Driver(feature_name="HAS_DIABETES", contribution=0.2, direction="increases_risk")
    ]
    node(state)

    assert fake_agent.last_conversation is not None
    human_seed = fake_agent.last_conversation[1]
    assert "HAS_DIABETES" in str(human_seed.content)
