"""Logging is provided by `zarreh_agentkit.observability` (extracted substrate);
this module re-exports it so existing `cohort.observability` imports keep
working."""

from functools import lru_cache

from langchain_core.callbacks import BaseCallbackHandler
from langsmith import Client
from zarreh_agentkit.observability import configure_logging, get_logger

__all__ = ["build_tracing_callbacks", "configure_logging", "get_logger"]


@lru_cache
def _langsmith_client(api_key: str) -> Client:
    return Client(api_key=api_key)


def build_tracing_callbacks(api_key: str, project: str) -> list[BaseCallbackHandler]:
    """Tracer bound to the configured key. The agentkit version relies on an
    ambient LANGSMITH_API_KEY, which pydantic's `.env` loading never exports,
    so every trace upload was rejected with a 401."""
    if not api_key:
        return []
    from langchain_core.tracers.langchain import LangChainTracer

    return [LangChainTracer(project_name=project, client=_langsmith_client(api_key))]
