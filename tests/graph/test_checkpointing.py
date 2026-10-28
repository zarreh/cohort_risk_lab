import logging
from ipaddress import IPv4Address

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from cohort.graph.checkpointing import build_checkpoint_serializer
from cohort.schemas.case_brief import CaseBrief, CorroboratingEvidence, Driver


def _brief() -> CaseBrief:
    return CaseBrief(
        patient_id="p1",
        narrative="Recent ED visits.",
        drivers=[Driver(feature_name="age", contribution=0.1, direction="increases_risk")],
        corroborating_evidence=[CorroboratingEvidence(source="lab", description="GFR 30")],
        care_gaps=[],
        missing_data=[],
        what_would_change_this="A normal GFR.",
    )


class _NotInState(BaseModel):
    value: int


def test_state_types_round_trip_without_unregistered_type_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    serde = build_checkpoint_serializer()
    state = {
        "draft_brief": _brief(),
        "drivers": [Driver(feature_name="age", contribution=0.1, direction="increases_risk")],
        "messages": [AIMessage(content="done")],
    }

    with caplog.at_level(logging.WARNING, logger="langgraph"):
        restored = serde.loads_typed(serde.dumps_typed(state))

    assert "unregistered type" not in caplog.text
    assert restored["draft_brief"] == state["draft_brief"]
    assert restored["drivers"] == state["drivers"]
    assert restored["messages"][0].content == "done"


def test_types_outside_the_state_are_not_rebuilt() -> None:
    serde = build_checkpoint_serializer()

    restored = serde.loads_typed(serde.dumps_typed({"x": _NotInState(value=1)}))

    assert not isinstance(restored["x"], _NotInState)


def test_builtin_safe_types_still_allowed() -> None:
    serde = build_checkpoint_serializer()

    restored = serde.loads_typed(serde.dumps_typed({"ip": IPv4Address("10.0.0.1")}))

    assert restored["ip"] == IPv4Address("10.0.0.1")
