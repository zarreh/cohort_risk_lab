"""Pure LCEL runnable: writes the draft case brief from the evidence
conversation. Structured output means there is no free-text field for a
decision to hide in except `narrative` and `what_would_change_this` — both
checked by `guardrails/no_decision_guard.py` after this chain runs.
"""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from cohort.graph.protocols import BriefWriterChain
from cohort.prompts.loader import load_prompt
from cohort.schemas.case_brief import CaseBrief


def build_brief_writer_chain(model: BaseChatModel) -> BriefWriterChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_prompt("brief_writer_v1")),
            MessagesPlaceholder("messages"),
        ]
    )
    # with_structured_output's stub return type is broader than the concrete
    # Pydantic model it actually produces at runtime.
    return cast(BriefWriterChain, prompt | model.with_structured_output(CaseBrief))
