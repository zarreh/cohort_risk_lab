"""Read-only access to `data/cohort.db`, built by
`data/build_cohort_store.py`. Every method returns typed records from
`store/models.py` — no tool or agent code ever sees a raw SQLite row or a
raw pandas frame.

Deliberately narrow: this is exactly the set of queries the tools in
`cohort.tools` need, not a general-purpose query interface. Adding a method
here should mean a tool needs it, not "it might be useful someday."
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from cohort.store.models import Condition, Encounter, LabObservation, Medication, PatientRecord

_MAX_ROWS_PER_QUERY = 200


class CohortStore:
    def __init__(self, db_path: Path) -> None:
        # check_same_thread=False: LangGraph's ToolNode runs sync tools in a
        # worker thread pool; this store is read-only, so cross-thread use is safe.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def get_patient(self, patient_id: str) -> PatientRecord | None:
        row = self._conn.execute(
            "SELECT PATIENT_ID, RACE, ETHNICITY, GENDER, MARITAL, INCOME "
            "FROM patients WHERE PATIENT_ID = ?",
            (patient_id,),
        ).fetchone()
        if row is None:
            return None
        return PatientRecord(
            patient_id=row["PATIENT_ID"],
            race=row["RACE"],
            ethnicity=row["ETHNICITY"],
            gender=row["GENDER"],
            marital=row["MARITAL"],
            income=row["INCOME"],
        )

    def get_conditions(self, patient_id: str) -> list[Condition]:
        rows = self._conn.execute(
            "SELECT PATIENT, START, STOP, DESCRIPTION FROM conditions "
            "WHERE PATIENT = ? ORDER BY START DESC LIMIT ?",
            (patient_id, _MAX_ROWS_PER_QUERY),
        ).fetchall()
        return [
            Condition(
                patient_id=row["PATIENT"],
                start=datetime.fromisoformat(row["START"]),
                stop=datetime.fromisoformat(row["STOP"]) if row["STOP"] else None,
                description=row["DESCRIPTION"],
            )
            for row in rows
        ]

    def get_recent_encounters(self, patient_id: str, limit: int = 20) -> list[Encounter]:
        rows = self._conn.execute(
            "SELECT PATIENT, START, STOP, ENCOUNTERCLASS, DESCRIPTION, TOTAL_CLAIM_COST "
            "FROM encounters WHERE PATIENT = ? ORDER BY START DESC LIMIT ?",
            (patient_id, min(limit, _MAX_ROWS_PER_QUERY)),
        ).fetchall()
        return [
            Encounter(
                patient_id=row["PATIENT"],
                start=datetime.fromisoformat(row["START"]),
                stop=datetime.fromisoformat(row["STOP"]) if row["STOP"] else None,
                encounter_class=row["ENCOUNTERCLASS"],
                description=row["DESCRIPTION"],
                total_claim_cost=row["TOTAL_CLAIM_COST"],
            )
            for row in rows
        ]

    def get_medications(self, patient_id: str, active_only: bool = False) -> list[Medication]:
        query = "SELECT PATIENT, START, STOP, DESCRIPTION FROM medications WHERE PATIENT = ?"
        if active_only:
            query += " AND STOP IS NULL"
        query += " ORDER BY START DESC LIMIT ?"
        rows = self._conn.execute(query, (patient_id, _MAX_ROWS_PER_QUERY)).fetchall()
        return [
            Medication(
                patient_id=row["PATIENT"],
                start=datetime.fromisoformat(row["START"]),
                stop=datetime.fromisoformat(row["STOP"]) if row["STOP"] else None,
                description=row["DESCRIPTION"],
            )
            for row in rows
        ]

    def get_recent_labs(self, patient_id: str, limit: int = 20) -> list[LabObservation]:
        rows = self._conn.execute(
            "SELECT PATIENT, DATE, CATEGORY, DESCRIPTION, VALUE, UNITS FROM observations "
            "WHERE PATIENT = ? ORDER BY DATE DESC LIMIT ?",
            (patient_id, min(limit, _MAX_ROWS_PER_QUERY)),
        ).fetchall()
        return [
            LabObservation(
                patient_id=row["PATIENT"],
                date=datetime.fromisoformat(row["DATE"]),
                category=row["CATEGORY"],
                description=row["DESCRIPTION"],
                value=str(row["VALUE"]),
                units=row["UNITS"],
            )
            for row in rows
        ]
