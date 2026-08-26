"""Four named, hand-authored clinical vignettes for `validation/canonical_scenarios.py`.

Same schema-matching pattern as `tests/fixtures/cohort_db.py`, extended
with two more patients. Hand-authored rather than mined from the real
frozen Synthea sample deliberately: a Synthea-simulated diabetic patient
is *always* given a glucose test in the same run that gave them the
diagnosis, so "diabetic with no glucose lab ever recorded" — the canonical
care-gap example this whole tool exists to catch — does not occur naturally
anywhere in the generated cohort. Testing it honestly requires a
constructed vignette; that is what a canonical scenario is for.

- `p_gap`      active diabetes, a blood-pressure vital, no glucose lab -> a care gap must fire.
- `p_nogap`    active diabetes AND a recent glucose lab -> no care gap.
- `p_low`      no conditions, one routine encounter -> nothing to flag.
- `p_missing`  no recorded data in any table at all -> every category
  must be reported missing, not silently treated as normal.
"""

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

_DATA = """
INSERT INTO patients VALUES
    ('p_gap', 'black', 'nonhispanic', 'F', 'M', 41000.0);
INSERT INTO patients VALUES
    ('p_nogap', 'white', 'nonhispanic', 'M', 'M', 58000.0);
INSERT INTO patients VALUES
    ('p_low', 'asian', 'nonhispanic', 'F', NULL, 72000.0);
INSERT INTO patients VALUES
    ('p_missing', 'native', 'nonhispanic', 'M', NULL, 30000.0);

INSERT INTO conditions VALUES
    ('p_gap', '2022-01-01T00:00:00', NULL, 'Diabetes mellitus type 2 (disorder)');
INSERT INTO conditions VALUES
    ('p_nogap', '2021-03-01T00:00:00', NULL, 'Diabetes mellitus type 2 (disorder)');

INSERT INTO encounters VALUES
    ('p_gap', '2023-06-01T09:00:00', '2023-06-01T09:30:00', 'wellness', 'Wellness visit', 150.0);
INSERT INTO encounters VALUES
    ('p_nogap', '2023-07-01T09:00:00', '2023-07-01T09:45:00', 'outpatient',
     'Diabetes follow-up', 220.0);
INSERT INTO encounters VALUES
    ('p_low', '2023-04-01T09:00:00', '2023-04-01T09:20:00', 'wellness', 'Annual physical', 120.0);

INSERT INTO medications VALUES
    ('p_gap', '2022-02-01T00:00:00', NULL, 'Metformin 500 MG');
INSERT INTO medications VALUES
    ('p_nogap', '2021-03-15T00:00:00', NULL, 'Metformin 500 MG');

INSERT INTO observations VALUES
    ('p_gap', '2023-06-01T09:10:00', 'vital-signs', 'Systolic Blood Pressure', '128', 'mmHg');
INSERT INTO observations VALUES
    ('p_nogap', '2023-07-01T09:10:00', 'laboratory',
     'Glucose [Mass/volume] in Blood', '110', 'mg/dL');
"""


def build_scenario_store(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA + _DATA)
    conn.commit()
    conn.close()
