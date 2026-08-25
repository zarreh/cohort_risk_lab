"""Structural (Protocol) types for the LLM-backed pieces nodes depend on.

Node factories accept these instead of concrete `Runnable[...]` types so a
plain test double (with just a matching `.invoke()`) can stand in without
subclassing LangChain's `Runnable` — real chains satisfy them structurally
too. This is what makes the graph's deterministic wiring and routing
testable without a live LLM API key.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from langchain_core.messages import BaseMessage

from cohort.schemas.case_brief import CaseBrief


class BriefWriterChain(Protocol):
    def invoke(self, input: dict[str, object]) -> CaseBrief: ...


class EvidenceAgent(Protocol):
    def invoke(self, messages: Sequence[BaseMessage]) -> BaseMessage: ...
