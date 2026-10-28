"""Scores the whole cohort with the deployed model and enqueues every
patient above its threshold into the review queue — the batch-scoring step
a real deployment would run periodically (nightly, say), separated here
from the interactive API so starting the server never blocks on rescoring
30,000+ patients.

Destructive by design: it first clears every existing case, review event
and LangGraph checkpoint, so the queue always matches the cohort currently
on disk. Rerun it after every `make data`, and stop the API first.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from cohort.api.deps import DEPLOYED_MODEL_VERSION
from cohort.pipeline.models.train import FEATURE_COLUMNS, build_scored_feature_table
from cohort.pipeline.registry import load_model_artifact
from cohort.settings import get_settings
from cohort.store.queue_store import QueueStore

# Tables LangGraph's SqliteSaver / AsyncSqliteSaver create.
_CHECKPOINT_TABLES = ("checkpoints", "writes")


def living_patient_ids(patients: pd.DataFrame) -> set[str]:
    """Care-management enrolment is meaningless for a patient with a recorded death."""
    return set(patients.loc[patients["DEATHDATE"].isna(), "PATIENT_ID"])


def clear_checkpoints(checkpoint_db_path: Path) -> None:
    """Drops paused review state, which is keyed by patient_id and would
    otherwise outlive the queue reset. Deletes rows rather than the file so
    the database's WAL/SHM side files stay consistent."""
    if not checkpoint_db_path.exists():
        return
    conn = sqlite3.connect(checkpoint_db_path)
    try:
        existing = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        with conn:
            for table in _CHECKPOINT_TABLES:
                if table in existing:
                    conn.execute(f"DELETE FROM {table}")  # table names come from a fixed allowlist
    finally:
        conn.close()


def select_cases(
    features: pd.DataFrame, scores: np.ndarray, threshold: float, living: set[str]
) -> list[tuple[str, float, str]]:
    """Patients at or above the deployed threshold who are still alive.
    `scores` is positionally aligned with `features`' rows."""
    mask = (scores >= threshold) & features["PATIENT_ID"].isin(living).to_numpy()
    selected_ids = features["PATIENT_ID"].to_numpy()[mask]
    selected_scores = scores[mask]
    return [
        (str(pid), float(score), "high")
        for pid, score in zip(selected_ids, selected_scores, strict=True)
    ]


def main() -> None:
    settings = get_settings()
    patients, features = build_scored_feature_table()
    living = living_patient_ids(patients)

    version_dir = Path(settings.registry_dir) / DEPLOYED_MODEL_VERSION
    pipeline, metadata = load_model_artifact(version_dir)

    scores = pipeline.predict_proba(features[FEATURE_COLUMNS])[:, 1]
    cases = select_cases(features, scores, metadata.threshold, living)

    queue_store = QueueStore(Path(settings.queue_store_path))
    try:
        queue_store.reset()
        clear_checkpoints(Path(settings.checkpoint_db_path))
        enqueued = queue_store.enqueue_cases(cases)
    finally:
        queue_store.close()

    print(f"Enqueued {enqueued:,} of {len(features):,} patients (threshold {metadata.threshold})")


if __name__ == "__main__":
    main()
