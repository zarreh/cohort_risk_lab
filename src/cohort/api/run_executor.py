"""Runs one case review, persisting every node event to the QueueStore as
it happens — so a review is replayable whether a client is watching live
or reconnects later. Same reasoning as A2's `run_executor.py`, adapted for
a graph that pauses at `interrupt()` instead of running to completion in
one pass: this function stops the moment the graph interrupts, and
`resume_review` is the separate entrypoint that continues it.
"""

from __future__ import annotations

import json

import structlog
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from cohort.graph.builder import CaseReviewGraph
from cohort.graph.state import CaseReviewState, create_initial_case_review_state
from cohort.observability import build_tracing_callbacks, get_logger
from cohort.settings import Settings
from cohort.store.queue_store import QueueStore

logger = get_logger(__name__)

_GRAPH_NODE_NAMES = frozenset(
    {
        "load_case",
        "assemble_evidence",
        "tools",
        "draft_brief",
        "verify_brief",
        "await_decision",
        "record_decision",
    }
)


def _json_default(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return str(value)


async def _stream_and_persist(
    graph: CaseReviewGraph,
    stream_input: CaseReviewState | Command[object],
    patient_id: str,
    queue_store: QueueStore,
    settings: Settings,
    sequence_start: int,
) -> int:
    """Shared streaming loop for both starting and resuming a review.
    Returns the next unused event sequence number."""
    callbacks = build_tracing_callbacks(settings.langsmith_api_key, settings.langsmith_project)
    config = RunnableConfig(
        configurable={"thread_id": patient_id},
        callbacks=callbacks,
        metadata={"correlation_id": patient_id},
    )
    sequence = sequence_start

    async for event in graph.astream_events(stream_input, version="v2", config=config):
        if event["event"] != "on_chain_end":
            continue
        metadata = event.get("metadata") or {}
        node_name = metadata.get("langgraph_node")
        if node_name not in _GRAPH_NODE_NAMES or event.get("name") != node_name:
            continue

        output = event.get("data", {}).get("output")
        queue_store.append_event(
            patient_id, sequence, node_name, json.dumps(output, default=_json_default)
        )
        sequence += 1

    return sequence


async def start_review(
    patient_id: str,
    graph: CaseReviewGraph,
    queue_store: QueueStore,
    settings: Settings,
) -> None:
    """Runs a review from the start until it either interrupts (awaiting a
    clinician's decision) or fails. Never runs to a terminal "completed"
    state on its own — `record_decision` only runs after a human resumes it."""
    structlog.contextvars.bind_contextvars(correlation_id=patient_id)
    try:
        queue_store.set_status(patient_id, "in_review")
        await _stream_and_persist(
            graph,
            create_initial_case_review_state(patient_id),
            patient_id,
            queue_store,
            settings,
            sequence_start=0,
        )
        queue_store.set_status(patient_id, "awaiting_decision")
    except Exception as exc:
        logger.error("review_failed", patient_id=patient_id, error=str(exc))
        queue_store.set_status(patient_id, "pending")
        raise
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")


async def resume_review(
    patient_id: str,
    decision: str,
    notes: str | None,
    graph: CaseReviewGraph,
    queue_store: QueueStore,
    settings: Settings,
) -> None:
    """Resumes an interrupted review with the clinician's decision and
    runs it to completion (`record_decision`)."""
    structlog.contextvars.bind_contextvars(correlation_id=patient_id)
    try:
        existing_events = queue_store.get_events(patient_id)
        next_sequence = len(existing_events)
        await _stream_and_persist(
            graph,
            Command(resume={"decision": decision, "notes": notes}),
            patient_id,
            queue_store,
            settings,
            sequence_start=next_sequence,
        )
        queue_store.record_decision(patient_id, decision, notes)
    except Exception as exc:
        logger.error("review_resume_failed", patient_id=patient_id, error=str(exc))
        raise
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")
