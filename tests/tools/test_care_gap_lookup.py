from pathlib import Path

import pytest

from cohort.store.cohort_store import CohortStore
from cohort.tools.care_gap_lookup import build_care_gap_lookup_tool
from tests.fixtures.cohort_db import build_test_cohort_db


@pytest.fixture
def store(tmp_path: Path) -> CohortStore:
    db_path = tmp_path / "test_cohort.db"
    build_test_cohort_db(db_path)
    return CohortStore(db_path)


def test_flags_missing_glucose_lab_for_diabetic_patient(store: CohortStore) -> None:
    tool = build_care_gap_lookup_tool(store)
    gaps = tool.invoke({"patient_id": "p1"})
    assert len(gaps) == 1
    assert "glucose" in gaps[0]["gap_description"].lower()


def test_no_gap_for_patient_without_the_matching_condition(store: CohortStore) -> None:
    tool = build_care_gap_lookup_tool(store)
    gaps = tool.invoke({"patient_id": "p2"})
    assert gaps == []
