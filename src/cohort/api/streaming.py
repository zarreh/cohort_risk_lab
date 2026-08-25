"""Bridges a case review's persisted events to Server-Sent Events.

Replays every event already in the QueueStore, then — if the case is still
`in_review` — tails newly-appended events until it reaches a terminal
status (`awaiting_decision` or back to `pending` on failure). Works
identically whether a client connects the instant a review starts or
reconnects long after the graph already interrupted (same discipline as
A2's `stream_investigation_events`).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from cohort.store.queue_store import QueueStore

_POLL_INTERVAL_SECONDS = 0.25
_ACTIVE_STATUSES = frozenset({"in_review"})


async def stream_review_events(queue_store: QueueStore, patient_id: str) -> AsyncIterator[str]:
    last_sequence = -1
    while True:
        events = queue_store.get_events(patient_id, after_sequence=last_sequence)
        for event in events:
            yield json.dumps({"node": event.node, "output": json.loads(event.payload_json)})
            last_sequence = event.sequence

        case = queue_store.get_case(patient_id)
        if case is None or case.status not in _ACTIVE_STATUSES:
            break
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    status = case.status if case is not None else "not_found"
    yield json.dumps({"node": "__end__", "output": {"status": status}})
