from pathlib import Path

import pytest

from cohort.store.cohort_store import CohortStore
from cohort.tools.patient_labs import build_patient_labs_tool
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture
def store(tmp_path: Path) -> CohortStore:
    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    return CohortStore(db_path)


def test_returns_projected_lab_fields(store: CohortStore) -> None:
    tool = build_patient_labs_tool(store)
    result = tool.invoke({"patient_id": "p2"})
    assert len(result) == 1
    assert set(result[0].keys()) == {"date", "category", "description", "value", "units"}
    assert "patient_id" not in result[0]
