"""Builds the SQLite store the running app reads at request time
(`cohort.store.cohort_store.CohortStore`) from the de-identified parquet
tables — a proper indexed database instead of scanning multi-million-row
parquet files per patient lookup.

Reads every table in row-group batches via pyarrow rather than
`pd.read_parquet` in one call. `observations.parquet` alone is 16M+ rows
after filtering; loading it into a single pandas DataFrame first and then
calling `to_sql` (even with `chunksize` on the *write* side) held the whole
frame in memory before writing a single row and OOM-killed the process on
this machine (14GB RAM) — confirmed via `dmesg`, twice, not a guess.
Batching the *read* keeps peak memory bounded regardless of table size.

Observations are restricted to `laboratory` and `vital-signs` categories:
the other categories Synthea emits (survey, social-history, exam, ...)
aren't clinically relevant to a case-review evidence tool and `survey`
alone is 8M+ rows — filtering here keeps the store small without touching
the training pipeline's own data path (`pipeline/`), which never reads
this database at all (D-A12-1: the pipeline is model-only).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent
DEIDENTIFIED_DIR = REPO_ROOT / "data" / "interim" / "deidentified"
COHORT_PATH = REPO_ROOT / "data" / "cohort" / "cohort.parquet"
DB_PATH = REPO_ROOT / "data" / "cohort.db"

RELEVANT_OBSERVATION_CATEGORIES = ("laboratory", "vital-signs")
BATCH_ROWS = 200_000


def _write_table_batched(
    conn: sqlite3.Connection,
    name: str,
    parquet_path: Path,
    index_columns: list[str],
    row_filter: str | None = None,
) -> int:
    """Streams `parquet_path` into SQLite table `name` in row-group
    batches, never holding more than `BATCH_ROWS` rows in memory at once."""
    parquet_file = pq.ParquetFile(parquet_path)
    total_rows = 0
    first_batch = True

    for batch in parquet_file.iter_batches(batch_size=BATCH_ROWS):
        df = batch.to_pandas()
        if row_filter is not None:
            df = df.query(row_filter)
        if df.empty:
            continue
        df.to_sql(name, conn, if_exists="replace" if first_batch else "append", index=False)
        total_rows += len(df)
        first_batch = False

    if first_batch:
        raise RuntimeError(f"No rows written for table {name!r} — check row_filter")

    for column in index_columns:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{name}_{column} ON {name}({column})")
    return total_rows


def build_cohort_store() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)

    n = _write_table_batched(conn, "patients", COHORT_PATH, index_columns=["PATIENT_ID"])
    print(f"patients: {n:,} rows")

    n = _write_table_batched(
        conn, "conditions", DEIDENTIFIED_DIR / "conditions.parquet", index_columns=["PATIENT"]
    )
    print(f"conditions: {n:,} rows")

    n = _write_table_batched(
        conn, "encounters", DEIDENTIFIED_DIR / "encounters.parquet", index_columns=["PATIENT"]
    )
    print(f"encounters: {n:,} rows")

    n = _write_table_batched(
        conn, "medications", DEIDENTIFIED_DIR / "medications.parquet", index_columns=["PATIENT"]
    )
    print(f"medications: {n:,} rows")

    n = _write_table_batched(
        conn,
        "observations",
        DEIDENTIFIED_DIR / "observations.parquet",
        index_columns=["PATIENT"],
        row_filter=f"CATEGORY in {RELEVANT_OBSERVATION_CATEGORIES!r}",
    )
    print(f"observations: {n:,} rows")

    conn.commit()
    conn.close()
    print(f"Built {DB_PATH} ({DB_PATH.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    build_cohort_store()
