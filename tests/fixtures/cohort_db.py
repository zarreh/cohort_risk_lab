"""A tiny in-memory-backed SQLite cohort store, matching the schema
`data/build_cohort_store.py` produces, for fast tool/store tests that
don't need the real multi-gigabyte database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE patients (
    PATIENT_ID TEXT, RACE TEXT, ETHNICITY TEXT,
    GENDER TEXT, MARITAL TEXT, INCOME REAL
);
CREATE TABLE conditions (
    PATIENT TEXT, START TEXT, STOP TEXT, DESCRIPTION TEXT
);
CREATE TABLE encounters (
    PATIENT TEXT, START TEXT, STOP TEXT, ENCOUNTERCLASS TEXT,
    DESCRIPTION TEXT, TOTAL_CLAIM_COST REAL
);
CREATE TABLE medications (
    PATIENT TEXT, START TEXT, STOP TEXT, DESCRIPTION TEXT
);
CREATE TABLE observations (
    PATIENT TEXT, DATE TEXT, CATEGORY TEXT,
    DESCRIPTION TEXT, VALUE TEXT, UNITS TEXT
);
"""

# p1: active diabetes, a blood-pressure vital but no glucose lab -> a care
# gap should fire. p2: no conditions recorded, has a glucose lab.
_DATA = """
INSERT INTO patients VALUES
    ('p1', 'black', 'nonhispanic', 'F', 'M', 45000.0);
INSERT INTO patients VALUES
    ('p2', 'white', 'nonhispanic', 'M', NULL, 60000.0);

INSERT INTO conditions VALUES
    ('p1', '2022-01-01T00:00:00', NULL, 'Diabetes mellitus type 2 (disorder)');
INSERT INTO conditions VALUES
    ('p1', '2020-01-01T00:00:00', '2020-06-01T00:00:00', 'Acute bronchitis (disorder)');

INSERT INTO encounters VALUES
    ('p1', '2023-06-01T09:00:00', '2023-06-01T09:30:00', 'wellness', 'Wellness visit', 150.0);
INSERT INTO encounters VALUES
    ('p2', '2023-05-01T09:00:00', '2023-05-01T09:30:00', 'outpatient', 'Follow-up', 200.0);

INSERT INTO medications VALUES
    ('p1', '2022-02-01T00:00:00', NULL, 'Metformin 500 MG');

INSERT INTO observations VALUES
    ('p1', '2023-06-01T09:10:00', 'vital-signs', 'Systolic Blood Pressure', '128', 'mmHg');
INSERT INTO observations VALUES
    ('p2', '2023-05-01T09:10:00', 'laboratory', 'Glucose [Mass/volume] in Blood', '95', 'mg/dL');
"""


def build_test_cohort_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA + _DATA)
    conn.commit()
    conn.close()
