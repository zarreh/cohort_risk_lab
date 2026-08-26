"""Builds the frozen validation fixture from the real, locally-generated
Synthea cohort — a seeded, stratified sub-sample of patients, not
hand-invented data.

`make validate` must run in CI without a JDK, without downloading Synthea,
and without regenerating a 30k-patient cohort on every PR — but "ML metric
floors on a frozen split" (docs/PLAN.md, Phase 9) only means something if
the split is real, de-identified, synthetic patient data run through the
actual pipeline, not fixtures invented to make a floor pass. So this
script is run once, locally, against a real `make data` output, and its
result is committed: a small (stratified by RACE, so the small strata and
the access-gap-affected `black` stratum both survive the sample) slice of
the same four de-identified event tables `cohort.pipeline.models.train`
reads, plus the matching post-access-gap-injection cohort aggregate.

Deliberately does not build a SQLite cohort store: `validation.metric_floors`
only ever reads these parquet tables through the real feature/label
pipeline, and `validation.canonical_scenarios` needs hand-authored
vignettes (`fixtures/scenario_patients.py`), not real patients — see that
module's docstring for why. An earlier version of this script did build a
store from the full observations table for every sampled patient and
produced a 737MB SQLite file; nothing in the validation harness actually
needs it, so it was removed rather than shrunk.

Not part of `make data` — this only needs to be re-run if the frozen
fixture itself should be regenerated (e.g. a new Synthea run with a
different seed). Committed fixture output lives in `validation/fixtures/`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEIDENTIFIED_DIR = REPO_ROOT / "data" / "interim" / "deidentified"
COHORT_PATH = REPO_ROOT / "data" / "cohort" / "cohort.parquet"

FIXTURE_DIR = Path(__file__).resolve().parent
FIXTURE_DEIDENTIFIED_DIR = FIXTURE_DIR / "deidentified"
FIXTURE_COHORT_PATH = FIXTURE_DIR / "cohort" / "cohort.parquet"

RANDOM_STATE = 42

# Per-stratum sample caps. Small strata (native, hawaiian) are kept in
# full: at real-world size they already sit near or below the fairness
# audit's `min_n` policy, and that boundary behaviour is exactly what the
# metric floors need to exercise honestly rather than average away.
RACE_SAMPLE_CAPS = {
    "white": 2000,
    "black": 900,
    "asian": 700,
    "other": 401,
    "hawaiian": 382,
    "native": 154,
}


def _sample_patient_ids(patients: pd.DataFrame) -> pd.Series:
    parts = []
    for race, group in patients.groupby("RACE"):
        cap = RACE_SAMPLE_CAPS.get(str(race), 200)
        n = min(cap, len(group))
        parts.append(group.sample(n=n, random_state=RANDOM_STATE)["Id"])
    return pd.concat(parts, ignore_index=True)


def _filter_and_write(parquet_path: Path, id_column: str, ids: pd.Series, out_path: Path) -> int:
    df = pd.read_parquet(parquet_path)
    filtered = df[df[id_column].isin(ids)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_parquet(out_path, index=False)
    return len(filtered)


def main() -> None:
    patients = pd.read_parquet(DEIDENTIFIED_DIR / "patients.parquet")
    ids = _sample_patient_ids(patients)
    print(f"sampled {len(ids):,} of {len(patients):,} patients")

    out_path = FIXTURE_DEIDENTIFIED_DIR / "patients.parquet"
    n = _filter_and_write(DEIDENTIFIED_DIR / "patients.parquet", "Id", ids, out_path)
    print(f"patients: {n:,}")
    for table in ("conditions", "encounters", "medications"):
        n = _filter_and_write(
            DEIDENTIFIED_DIR / f"{table}.parquet",
            "PATIENT",
            ids,
            FIXTURE_DEIDENTIFIED_DIR / f"{table}.parquet",
        )
        print(f"{table}: {n:,}")

    n = _filter_and_write(COHORT_PATH, "PATIENT_ID", ids, FIXTURE_COHORT_PATH)
    print(f"cohort: {n:,}")


if __name__ == "__main__":
    main()
