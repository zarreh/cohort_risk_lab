"""Bridges a case review's persisted events to Server-Sent Events.

Replays every event already in the QueueStore, then — if the case is still
`in_review` — tails newly-appended events until it reaches a terminal
status (`awaiting_decision` or back to `pending` on failure). Works
identically whether a client connects the instant a review starts or
reconnects long after the graph already interrupted (same discipline as
A2's `stream_investigation_events`).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import partial
from typing import Any

from zarreh_agentkit.runs import replay_and_tail

from cohort.store.queue_store import QueueStore

_ACTIVE_STATUSES = frozenset({"in_review"})


def stream_review_events(queue_store: QueueStore, patient_id: str) -> AsyncIterator[str]:
    def poll_end() -> dict[str, Any] | None:
        case = queue_store.get_case(patient_id)
        if case is not None and case.status in _ACTIVE_STATUSES:
            return None
        return {"status": case.status if case is not None else "not_found"}

    return replay_and_tail(partial(queue_store.get_events, patient_id), poll_end)
