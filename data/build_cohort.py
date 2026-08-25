"""Assembles the de-identified per-table parquet files into one compact,
patient-level cohort store (docs/PLAN.md §Phases, Phase 1).

Deliberately stops short of feature engineering: this script's only job is
"one clean, joinable table per patient plus the event tables that support
it", keyed on the same PATIENT id throughout. Turning that into a
leakage-safe feature/label matrix — choosing each patient's index date,
enforcing the lookback/forward-window split — is `pipeline/splits.py`'s job
(Phase 2), because that choice belongs to the modelling step, not the data
step, and redoing it must not require re-touching this script.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEIDENTIFIED_DIR = REPO_ROOT / "data" / "interim" / "deidentified"
COHORT_DIR = REPO_ROOT / "data" / "cohort"


def _summarize_conditions(conditions: pd.DataFrame) -> pd.DataFrame:
    active = conditions[conditions["STOP"].isna()]
    return (
        active.groupby("PATIENT")
        .size()
        .rename("ACTIVE_CONDITION_COUNT")
        .reset_index()
        .rename(columns={"PATIENT": "Id"})
    )


def _summarize_encounters(encounters: pd.DataFrame) -> pd.DataFrame:
    grouped = encounters.groupby("PATIENT").agg(
        ENCOUNTER_COUNT=("Id", "count"),
        TOTAL_CLAIM_COST=("TOTAL_CLAIM_COST", "sum"),
        TOTAL_PAYER_COVERAGE=("PAYER_COVERAGE", "sum"),
        LAST_ENCOUNTER_DATE=("START", "max"),
        FIRST_ENCOUNTER_DATE=("START", "min"),
    )
    return grouped.reset_index().rename(columns={"PATIENT": "Id"})


def _summarize_medications(medications: pd.DataFrame) -> pd.DataFrame:
    grouped = medications.groupby("PATIENT").agg(
        MEDICATION_COUNT=("CODE", "count"),
        MEDICATION_TOTAL_COST=("TOTALCOST", "sum"),
    )
    return grouped.reset_index().rename(columns={"PATIENT": "Id"})


def build_cohort() -> pd.DataFrame:
    patients = pd.read_parquet(DEIDENTIFIED_DIR / "patients.parquet")
    conditions = pd.read_parquet(DEIDENTIFIED_DIR / "conditions.parquet")
    encounters = pd.read_parquet(DEIDENTIFIED_DIR / "encounters.parquet")
    medications = pd.read_parquet(DEIDENTIFIED_DIR / "medications.parquet")

    cohort = patients.merge(_summarize_conditions(conditions), on="Id", how="left")
    cohort = cohort.merge(_summarize_encounters(encounters), on="Id", how="left")
    cohort = cohort.merge(_summarize_medications(medications), on="Id", how="left")

    count_cols = [
        "ACTIVE_CONDITION_COUNT",
        "ENCOUNTER_COUNT",
        "MEDICATION_COUNT",
        "TOTAL_CLAIM_COST",
        "TOTAL_PAYER_COVERAGE",
        "MEDICATION_TOTAL_COST",
    ]
    cohort[count_cols] = cohort[count_cols].fillna(0)

    return cohort.rename(columns={"Id": "PATIENT_ID"})


def main() -> None:
    COHORT_DIR.mkdir(parents=True, exist_ok=True)

    cohort = build_cohort()
    out_path = COHORT_DIR / "cohort.parquet"
    cohort.to_parquet(out_path, index=False)
    print(f"cohort: {len(cohort):,} patients, {cohort.shape[1]} columns -> {out_path}")
    print("Run data.inject_access_gap next — it also writes the committed data/sample/.")


if __name__ == "__main__":
    main()
