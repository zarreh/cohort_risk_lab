import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from data.populate_queue import clear_checkpoints, living_patient_ids, select_cases


def test_deceased_patients_are_never_queued() -> None:
    patients = pd.DataFrame(
        {
            "PATIENT_ID": ["alive-1", "dead-1", "alive-2"],
            "DEATHDATE": [None, "2021-06-27", None],
        }
    )

    assert living_patient_ids(patients) == {"alive-1", "alive-2"}


def test_select_cases_keeps_living_patients_at_or_above_threshold() -> None:
    features = pd.DataFrame({"PATIENT_ID": ["a", "b", "c", "d"]}, index=[10, 3, 7, 1])
    scores = np.array([0.9, 0.5, 0.95, 0.6])

    cases = select_cases(features, scores, threshold=0.6, living={"a", "b", "d"})

    assert cases == [("a", 0.9, "high"), ("d", 0.6, "high")]


def test_clear_checkpoints_ignores_missing_file(tmp_path: Path) -> None:
    clear_checkpoints(tmp_path / "missing.db")
    assert not (tmp_path / "missing.db").exists()


def test_clear_checkpoints_empties_langgraph_tables_only(tmp_path: Path) -> None:
    db = tmp_path / "checkpoints.db"
    conn = sqlite3.connect(db)
    for table in ("checkpoints", "writes", "unrelated"):
        conn.execute(f"CREATE TABLE {table} (x INTEGER)")
        conn.execute(f"INSERT INTO {table} VALUES (1)")
    conn.commit()
    conn.close()

    clear_checkpoints(db)

    conn = sqlite3.connect(db)
    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("checkpoints", "writes", "unrelated")
    }
    conn.close()
    assert counts == {"checkpoints": 0, "writes": 0, "unrelated": 1}
