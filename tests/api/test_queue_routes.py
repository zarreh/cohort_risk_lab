from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cohort.api import routes
from cohort.api.deps import get_case_review_graph, get_queue_store, get_scored_patient_ids
from cohort.api.main import app
from cohort.store.queue_store import QueueStore


@pytest.fixture
def queue_store(tmp_path: Path) -> QueueStore:
    return QueueStore(tmp_path / "test_queue.db")


@pytest.fixture
def client(queue_store: QueueStore) -> Iterator[TestClient]:
    app.dependency_overrides[get_queue_store] = lambda: queue_store
    # start/decision routes need a graph dependency to resolve even when the
    # test never reaches it (404/409 short-circuit before it's used).
    app.dependency_overrides[get_case_review_graph] = lambda: None
    app.dependency_overrides[get_scored_patient_ids] = lambda: frozenset({"p1", "p2"})
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_list_queue_empty(client: TestClient) -> None:
    response = client.get("/queue")
    assert response.status_code == 200
    assert response.json() == []


def test_list_queue_returns_enqueued_cases_sorted_by_risk(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    queue_store.enqueue_case("p2", risk_score=0.9, risk_tier="high")

    response = client.get("/queue")
    assert response.status_code == 200
    body = response.json()
    assert [entry["patient_id"] for entry in body] == ["p2", "p1"]


def test_get_case_404_for_unknown_patient(client: TestClient) -> None:
    response = client.get("/queue/nonexistent")
    assert response.status_code == 404


def test_get_case_returns_case_detail(client: TestClient, queue_store: QueueStore) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    response = client.get("/queue/p1")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_start_review_404_for_unknown_patient(client: TestClient) -> None:
    response = client.post("/queue/nonexistent/start")
    assert response.status_code == 404


def test_start_review_409_when_not_pending(client: TestClient, queue_store: QueueStore) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    queue_store.set_status("p1", "in_review")

    response = client.post("/queue/p1/start")
    assert response.status_code == 409


def test_decision_404_for_unknown_patient(client: TestClient) -> None:
    response = client.post("/queue/nonexistent/decision", json={"decision": "enrol"})
    assert response.status_code == 404


def test_decision_409_when_not_awaiting_decision(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")

    response = client.post("/queue/p1/decision", json={"decision": "enrol"})
    assert response.status_code == 409


def test_decision_rejects_invalid_decision_value(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    queue_store.set_status("p1", "awaiting_decision")

    response = client.post("/queue/p1/decision", json={"decision": "not_a_real_decision"})
    assert response.status_code == 422


async def _noop_task(*_args: object, **_kwargs: object) -> None:
    return None


@pytest.fixture
def no_background_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes.queue, "start_review", _noop_task)
    monkeypatch.setattr(routes.queue, "resume_review", _noop_task)


def test_start_review_404_when_patient_not_in_scored_cohort(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("stale", risk_score=0.5, risk_tier="high")

    response = client.post("/queue/stale/start")

    assert response.status_code == 404
    assert "scored cohort" in response.json()["detail"]
    case = queue_store.get_case("stale")
    assert case is not None
    assert case.status == "pending"


@pytest.mark.usefixtures("no_background_runs")
def test_start_review_claims_case_so_second_start_conflicts(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")

    first = client.post("/queue/p1/start")
    second = client.post("/queue/p1/start")

    assert first.status_code == 202
    assert second.status_code == 409
    case = queue_store.get_case("p1")
    assert case is not None
    assert case.status == "in_review"


@pytest.mark.usefixtures("no_background_runs")
def test_decision_claims_case_so_second_decision_conflicts(
    client: TestClient, queue_store: QueueStore
) -> None:
    queue_store.enqueue_case("p1", risk_score=0.5, risk_tier="high")
    queue_store.set_status("p1", "awaiting_decision")

    first = client.post("/queue/p1/decision", json={"decision": "enrol"})
    second = client.post("/queue/p1/decision", json={"decision": "decline"})

    assert first.status_code == 202
    assert second.status_code == 409
    case = queue_store.get_case("p1")
    assert case is not None
    assert case.status == "deciding"
