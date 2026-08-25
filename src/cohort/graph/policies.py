"""Model selection per node — never inline in a node (docs/PLAN.md §Phases).

`gpt-4o` for the evidence agent per PORTFOLIO_PLAN_V3.md's model table
("A12 evidence agent" is listed among the reasoning-heavy nodes); the
brief-writer chain can run on the cheaper model since structured synthesis
from already-gathered evidence is a lower-stakes generation than deciding
which tools to call next.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from cohort.settings import Settings

FAST_MODEL = "gpt-4o-mini"
REASONING_MODEL = "gpt-4o"


def _api_key(settings: Settings) -> SecretStr | None:
    return SecretStr(settings.openai_api_key) if settings.openai_api_key else None


def build_fast_model(settings: Settings) -> ChatOpenAI:
    """Brief writer — structured synthesis from evidence already gathered."""
    return ChatOpenAI(model=FAST_MODEL, temperature=0, api_key=_api_key(settings))


def build_reasoning_model(settings: Settings) -> ChatOpenAI:
    """Evidence agent — decides which tools to call and when evidence is
    sufficient."""
    return ChatOpenAI(model=REASONING_MODEL, temperature=0, api_key=_api_key(settings))
