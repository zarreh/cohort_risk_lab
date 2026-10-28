"""Serializer for persisted case-review checkpoints.

LangGraph's default serializer rebuilds *any* class named in a checkpoint and
only warns about types it doesn't know; a future LangGraph release blocks
them, which would break resuming a paused review. Listing the state's own
Pydantic models (`graph/state.py`) keeps resume working and limits what a
tampered checkpoint database could construct to these types plus LangGraph's
built-in safe set (messages, datetimes, ...).
"""

from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from cohort.schemas.case_brief import CaseBrief, CorroboratingEvidence, Driver

CHECKPOINT_STATE_TYPES = (CaseBrief, CorroboratingEvidence, Driver)


def build_checkpoint_serializer() -> JsonPlusSerializer:
    return JsonPlusSerializer(allowed_msgpack_modules=CHECKPOINT_STATE_TYPES)
