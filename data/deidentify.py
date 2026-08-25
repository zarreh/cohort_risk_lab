"""HIPAA Safe Harbor style de-identification of the raw Synthea export.

Applied even though the source data is already fully synthetic: the point
of this app is to demonstrate the discipline, not to skip it because the
underlying risk happens to be zero here (PORTFOLIO_PLAN_V3.md §7 G3
domain grounding).

Two transforms, both standard de-identification technique rather than
invented for this app:

1. **Direct identifiers dropped** — name, SSN, driver's licence, passport,
   street address, exact geocode, county, ZIP, birthplace. Of the Safe
   Harbor 18, only STATE (an explicitly permitted geographic unit) and the
   clinical/demographic fields the model and audit actually need survive.
2. **Per-patient date shifting** — every date in every table for a given
   patient is shifted by the same random offset, drawn deterministically
   from a seeded hash of that patient's id. This preserves every interval
   *within* one patient's history (which is what the temporal features in
   `pipeline/splits.py` need) while destroying any alignment *across*
   patients or with real calendar time — the standard technique behind
   Safe Harbor date de-identification (cf. PhysioNet MIMIC).

Ages over 89 are then capped at the Safe-Harbor-mandated "90" by moving the
(already-shifted) birthdate, so no downstream computation can ever recover
an exact age past that boundary.

Output is an intermediate, gitignored parquet set — never the artifact this
app publishes. `data/build_cohort.py` (next step) is what produces the
small sample that actually gets committed, and it re-checks these
guarantees before writing anything to `data/sample/`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "data" / "synthea.config.json"
RAW_DIR = REPO_ROOT / "data" / "synthea" / "csv"
OUT_DIR = REPO_ROOT / "data" / "interim" / "deidentified"

# Fixed "as of" date used only to decide the 90+ age cap after shifting —
# not a real calendar reference, and never exposed downstream.
ANALYSIS_DATE = pd.Timestamp("2025-01-01")
MAX_REPORTABLE_AGE_YEARS = 90
DATE_SHIFT_RANGE_DAYS = 365  # +/- one year, per patient

PATIENT_COLUMNS_KEPT = [
    "Id",
    "BIRTHDATE",
    "DEATHDATE",
    "MARITAL",
    "RACE",
    "ETHNICITY",
    "GENDER",
    "STATE",
    "HEALTHCARE_EXPENSES",
    "HEALTHCARE_COVERAGE",
    "INCOME",
]

# table filename -> (patient id column, [date columns to shift])
CLINICAL_TABLES: dict[str, tuple[str, list[str]]] = {
    "conditions.csv": ("PATIENT", ["START", "STOP"]),
    "medications.csv": ("PATIENT", ["START", "STOP"]),
    "encounters.csv": ("PATIENT", ["START", "STOP"]),
    "procedures.csv": ("PATIENT", ["START", "STOP"]),
    "observations.csv": ("PATIENT", ["DATE"]),
    "immunizations.csv": ("PATIENT", ["DATE"]),
}


def _patient_offset_days(patient_id: str, seed: int) -> int:
    """Deterministic per-patient shift in [-RANGE, +RANGE] days, derived
    from a seeded hash so the same seed always reproduces the same cohort
    without persisting a separate lookup table anywhere."""
    digest = hashlib.sha256(f"{seed}:{patient_id}".encode()).hexdigest()
    span = 2 * DATE_SHIFT_RANGE_DAYS + 1
    return int(digest, 16) % span - DATE_SHIFT_RANGE_DAYS


def _shift_dates(series: pd.Series, offsets: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed + pd.to_timedelta(offsets, unit="D")


def deidentify_patients(seed: int) -> pd.DataFrame:
    patients = pd.read_csv(RAW_DIR / "patients.csv", usecols=PATIENT_COLUMNS_KEPT)
    patients["OFFSET_DAYS"] = patients["Id"].map(lambda pid: _patient_offset_days(pid, seed))

    patients["BIRTHDATE"] = _shift_dates(patients["BIRTHDATE"], patients["OFFSET_DAYS"])
    patients["DEATHDATE"] = _shift_dates(patients["DEATHDATE"], patients["OFFSET_DAYS"])

    age_at_analysis = (ANALYSIS_DATE - patients["BIRTHDATE"].dt.tz_localize(None)).dt.days / 365.25
    capped_birthdate = ANALYSIS_DATE - pd.Timedelta(days=MAX_REPORTABLE_AGE_YEARS * 365.25)
    over_cap = age_at_analysis > MAX_REPORTABLE_AGE_YEARS
    patients.loc[over_cap, "BIRTHDATE"] = capped_birthdate.tz_localize("UTC")

    return patients


def deidentify_clinical_table(filename: str, offsets_by_patient: pd.Series) -> pd.DataFrame:
    patient_col, date_cols = CLINICAL_TABLES[filename]
    df = pd.read_csv(RAW_DIR / filename, low_memory=False)
    offsets = df[patient_col].map(offsets_by_patient)
    for col in date_cols:
        if col in df.columns:
            df[col] = _shift_dates(df[col], offsets)
    return df


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text())
    seed = int(config["seed"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    patients = deidentify_patients(seed)
    offsets_by_patient = patients.set_index("Id")["OFFSET_DAYS"]
    patients.drop(columns=["OFFSET_DAYS"]).to_parquet(OUT_DIR / "patients.parquet", index=False)
    print(f"patients: {len(patients):,} rows -> {OUT_DIR / 'patients.parquet'}")

    for filename in CLINICAL_TABLES:
        table = deidentify_clinical_table(filename, offsets_by_patient)
        out_path = OUT_DIR / filename.replace(".csv", ".parquet")
        table.to_parquet(out_path, index=False)
        print(f"{filename}: {len(table):,} rows -> {out_path}")


if __name__ == "__main__":
    main()
