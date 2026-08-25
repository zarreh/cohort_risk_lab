from pathlib import Path

import pytest

from cohort.store.cohort_store import CohortStore
from cohort.tools.patient_encounters import build_patient_encounters_tool
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture
def store(tmp_path: Path) -> CohortStore:
    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    return CohortStore(db_path)


def test_returns_projected_fields_only(store: CohortStore) -> None:
    tool = build_patient_encounters_tool(store)
    result = tool.invoke({"patient_id": "p1"})
    assert len(result) == 1
    assert set(result[0].keys()) == {"start", "encounter_class", "description"}
    assert "total_claim_cost" not in result[0]
    assert "patient_id" not in result[0]


def test_unknown_patient_returns_empty_list(store: CohortStore) -> None:
    tool = build_patient_encounters_tool(store)
    result = tool.invoke({"patient_id": "nonexistent"})
    assert result == []
