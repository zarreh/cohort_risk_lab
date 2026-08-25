"""ReAct step: invokes the tool-bound evidence agent on the running
conversation. Seeds the system message with the drivers `load_case`
already computed, so the agent gathers evidence *for* a score it did not
produce, rather than being asked to assess the patient itself.
"""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from cohort.graph.protocols import EvidenceAgent
from cohort.graph.state import CaseReviewState


def _seed_messages(state: CaseReviewState, system_prompt: str) -> list[BaseMessage]:
    driver_lines = "\n".join(
        f"- {d.feature_name}: {d.direction} (contribution {d.contribution:+.3f})"
        for d in state["drivers"]
    )
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                f"Patient {state['patient_id']} was flagged at risk tier "
                f"'{state['risk_tier']}' (score {state['risk_score']:.3f}).\n\n"
                f"Model drivers:\n{driver_lines}\n\n"
                "Gather corroborating evidence for these drivers."
            )
        ),
    ]


def build_assemble_evidence_node(
    evidence_agent: EvidenceAgent, system_prompt: str
) -> Callable[[CaseReviewState], dict[str, object]]:
    def assemble_evidence_node(state: CaseReviewState) -> dict[str, object]:
        seed = [] if state["messages"] else _seed_messages(state, system_prompt)
        conversation = [*state["messages"], *seed]
        response = evidence_agent.invoke(conversation)
        return {"messages": [*seed, response]}

    return assemble_evidence_node
