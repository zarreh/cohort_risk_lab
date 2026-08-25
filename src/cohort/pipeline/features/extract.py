"""Extracts one feature row per patient from lookback-window events only.

Leakage-safe by construction, not by convention: every input here is a
`lookback_*` frame produced by `pipeline/splits.py`, which already excludes
anything on or after a patient's `INDEX_DATE`. There is no cutoff logic in
this module to get wrong — the boundary is enforced once, upstream.

Deliberately excludes RACE and ETHNICITY from the feature set (docs/PLAN.md
§Phase 2 note, D-A12-4): the audit needs them as the stratification key,
not as a model input. The Obermeyer et al. finding this app reproduces did
*not* need race as an input feature to produce a racially disparate
outcome — the label choice alone was sufficient. Including race as a
feature would blur that point rather than sharpen it.

Statistical steps that must never see test data (imputation, scaling) are
deliberately *not* here — see `pipeline/features/preprocess.py`, which is
fit only inside CV folds.
"""

from __future__ import annotations

import pandas as pd

from cohort.pipeline.features.chronic_conditions import CHRONIC_CONDITION_KEYWORDS

# HIPAA Safe Harbor: no disclosed or model-facing age may exceed 89. Applied
# here (the feature actually fed to the model and, later, to explanations)
# rather than by mutating birthdates upstream — see data/deidentify.py's
# module docstring for why that approach was rejected.
MAX_REPORTABLE_AGE_YEARS = 90

NUMERIC_FEATURES = [
    "AGE_AT_INDEX",
    "LOOKBACK_ENCOUNTER_COUNT",
    "LOOKBACK_EMERGENCY_ENCOUNTER_COUNT",
    "LOOKBACK_INPATIENT_ENCOUNTER_COUNT",
    "LOOKBACK_TOTAL_CLAIM_COST",
    "LOOKBACK_MEDICATION_COUNT",
    "LOOKBACK_MEDICATION_TOTAL_COST",
    "LOOKBACK_ACTIVE_CONDITION_COUNT",
    "LOOKBACK_DISTINCT_CONDITION_COUNT",
    "INCOME",
]
CATEGORICAL_FEATURES = ["GENDER", "MARITAL"]
BINARY_FEATURES = list(CHRONIC_CONDITION_KEYWORDS.keys())


def _age_at_index(patients: pd.DataFrame, index_dates: pd.DataFrame) -> pd.Series:
    merged = index_dates[["PATIENT_ID", "INDEX_DATE"]].merge(
        patients[["PATIENT_ID", "BIRTHDATE"]], on="PATIENT_ID", how="left"
    )
    age = (merged["INDEX_DATE"] - merged["BIRTHDATE"]).dt.days / 365.25
    age = age.clip(lower=0, upper=MAX_REPORTABLE_AGE_YEARS)
    return pd.Series(age.to_numpy(), index=merged["PATIENT_ID"], name="AGE_AT_INDEX")


def _encounter_features(lookback_encounters: pd.DataFrame) -> pd.DataFrame:
    events = lookback_encounters.copy()
    events["IS_EMERGENCY"] = events["ENCOUNTERCLASS"] == "emergency"
    events["IS_INPATIENT"] = events["ENCOUNTERCLASS"] == "inpatient"

    return events.groupby("PATIENT").agg(
        LOOKBACK_ENCOUNTER_COUNT=("Id", "count"),
        LOOKBACK_TOTAL_CLAIM_COST=("TOTAL_CLAIM_COST", "sum"),
        LOOKBACK_EMERGENCY_ENCOUNTER_COUNT=("IS_EMERGENCY", "sum"),
        LOOKBACK_INPATIENT_ENCOUNTER_COUNT=("IS_INPATIENT", "sum"),
    )


def _medication_features(lookback_medications: pd.DataFrame) -> pd.DataFrame:
    return lookback_medications.groupby("PATIENT").agg(
        LOOKBACK_MEDICATION_COUNT=("CODE", "count"),
        LOOKBACK_MEDICATION_TOTAL_COST=("TOTALCOST", "sum"),
    )


def _condition_features(lookback_conditions: pd.DataFrame) -> pd.DataFrame:
    active = lookback_conditions[lookback_conditions["STOP"].isna()]
    grouped = lookback_conditions.groupby("PATIENT")

    features = pd.DataFrame(
        {
            "LOOKBACK_ACTIVE_CONDITION_COUNT": active.groupby("PATIENT").size(),
            "LOOKBACK_DISTINCT_CONDITION_COUNT": grouped["CODE"].nunique(),
        }
    )

    description = lookback_conditions["DESCRIPTION"].str.lower()
    for flag_name, keyword in CHRONIC_CONDITION_KEYWORDS.items():
        matching_patients = lookback_conditions.loc[
            description.str.contains(keyword, na=False), "PATIENT"
        ].unique()
        features[flag_name] = features.index.isin(matching_patients)

    return features


def build_feature_table(
    patients: pd.DataFrame,
    index_dates: pd.DataFrame,
    lookback_conditions: pd.DataFrame,
    lookback_encounters: pd.DataFrame,
    lookback_medications: pd.DataFrame,
) -> pd.DataFrame:
    """One row per included patient (`index_dates["INCLUDED"]`), indexed by
    PATIENT_ID, with every column in `NUMERIC_FEATURES + CATEGORICAL_FEATURES
    + BINARY_FEATURES` populated (0/False/NaN, never a missing column, for
    patients with no lookback events of a given kind)."""
    included = index_dates.loc[index_dates["INCLUDED"], ["PATIENT_ID"]].set_index("PATIENT_ID")

    age = _age_at_index(patients, index_dates)
    demographics = patients.set_index("PATIENT_ID")[["GENDER", "MARITAL", "INCOME"]]
    encounter_features = _encounter_features(lookback_encounters)
    medication_features = _medication_features(lookback_medications)
    condition_features = _condition_features(lookback_conditions)

    table = included.join(age).join(demographics).join(encounter_features)
    table = table.join(medication_features).join(condition_features)

    count_cols = [c for c in NUMERIC_FEATURES if c.startswith("LOOKBACK_")]
    table[count_cols] = table[count_cols].fillna(0.0)
    table[BINARY_FEATURES] = table[BINARY_FEATURES].fillna(False).astype(bool)

    return table.reset_index()
