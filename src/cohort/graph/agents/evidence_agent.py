"""A model + a tool set + a prompt id, nothing else (docs/PLAN.md §9.3).

The system prompt is injected once by `nodes/assemble_evidence.py` when the
ReAct loop begins — this module just binds the tools to the model.
"""

from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool

from cohort.graph.protocols import EvidenceAgent


def build_evidence_agent(model: BaseChatModel, tools: list[StructuredTool]) -> EvidenceAgent:
    return cast(EvidenceAgent, model.bind_tools(tools))
