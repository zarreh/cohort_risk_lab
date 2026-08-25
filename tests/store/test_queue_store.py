from pathlib import Path

import pytest

from cohort.store.queue_store import QueueStore


@pytest.fixture
def store(tmp_path: Path) -> QueueStore:
    return QueueStore(tmp_path / "test_queue.db")


def test_enqueue_and_get_case(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.82, risk_tier="high")
    case = store.get_case("p1")
    assert case is not None
    assert case.status == "pending"
    assert case.risk_score == 0.82


def test_enqueue_is_idempotent(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.82, risk_tier="high")
    store.enqueue_case("p1", risk_score=0.99, risk_tier="high")  # should not overwrite
    case = store.get_case("p1")
    assert case is not None
    assert case.risk_score == 0.82


def test_list_queue_orders_by_risk_score_descending(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    store.enqueue_case("p2", risk_score=0.9, risk_tier="high")
    store.enqueue_case("p3", risk_score=0.7, risk_tier="high")

    queue = store.list_queue()
    assert [c.patient_id for c in queue] == ["p2", "p3", "p1"]


def test_list_queue_filters_by_status(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    store.enqueue_case("p2", risk_score=0.9, risk_tier="high")
    store.set_status("p2", "in_review")

    pending = store.list_queue(status="pending")
    assert [c.patient_id for c in pending] == ["p1"]


def test_record_decision_updates_status_and_fields(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    store.record_decision("p1", "enrol", "Confirmed with clinician.")

    case = store.get_case("p1")
    assert case is not None
    assert case.status == "decided"
    assert case.decision == "enrol"
    assert case.override_notes == "Confirmed with clinician."
    assert case.decided_at is not None


def test_get_case_returns_none_for_unknown_patient(store: QueueStore) -> None:
    assert store.get_case("nonexistent") is None


def test_events_are_ordered_and_filterable_by_sequence(store: QueueStore) -> None:
    store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    store.append_event("p1", 0, "load_case", '{"risk_score": 0.5}')
    store.append_event("p1", 1, "assemble_evidence", "{}")

    all_events = store.get_events("p1")
    assert [e.node for e in all_events] == ["load_case", "assemble_evidence"]

    later_events = store.get_events("p1", after_sequence=0)
    assert [e.node for e in later_events] == ["assemble_evidence"]
