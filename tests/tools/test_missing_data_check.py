from pathlib import Path

import pytest

from cohort.store.cohort_store import CohortStore
from cohort.tools.missing_data_check import build_missing_data_check_tool
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture
def store(tmp_path: Path) -> CohortStore:
    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    return CohortStore(db_path)


def test_patient_with_all_data_types_has_nothing_missing(store: CohortStore) -> None:
    tool = build_missing_data_check_tool(store)
    result = tool.invoke({"patient_id": "p1"})
    assert result["missing_data_types"] == []


def test_patient_missing_conditions_and_medications(store: CohortStore) -> None:
    tool = build_missing_data_check_tool(store)
    result = tool.invoke({"patient_id": "p2"})
    assert set(result["missing_data_types"]) == {"conditions", "medications"}
