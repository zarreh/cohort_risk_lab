from pathlib import Path

import pytest

from cohort.store.cohort_store import CohortStore
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture
def store(tmp_path: Path) -> CohortStore:
    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    return CohortStore(db_path)


def test_get_patient_returns_typed_record(store: CohortStore) -> None:
    patient = store.get_patient("p1")
    assert patient is not None
    assert patient.race == "black"
    assert patient.income == 45000.0


def test_get_patient_returns_none_for_unknown_id(store: CohortStore) -> None:
    assert store.get_patient("nonexistent") is None


def test_get_conditions_orders_most_recent_first(store: CohortStore) -> None:
    conditions = store.get_conditions("p1")
    assert len(conditions) == 2
    assert conditions[0].start > conditions[1].start


def test_condition_is_active_reflects_null_stop(store: CohortStore) -> None:
    conditions = store.get_conditions("p1")
    active = [c for c in conditions if c.is_active]
    assert len(active) == 1
    assert "diabetes" in active[0].description.lower()


def test_get_medications_active_only_filters_stopped(store: CohortStore) -> None:
    all_meds = store.get_medications("p2")
    assert all_meds == []
    active_meds = store.get_medications("p1", active_only=True)
    assert len(active_meds) == 1


def test_get_recent_labs_returns_typed_records(store: CohortStore) -> None:
    labs = store.get_recent_labs("p2")
    assert len(labs) == 1
    assert labs[0].category == "laboratory"
