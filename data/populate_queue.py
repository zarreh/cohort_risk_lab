"""Scores the whole cohort with the deployed model and enqueues every
patient above its threshold into the review queue — the batch-scoring step
a real deployment would run periodically (nightly, say), separated here
from the interactive API so starting the server never blocks on rescoring
30,000+ patients.
"""

from __future__ import annotations

from pathlib import Path

from cohort.api.deps import DEPLOYED_MODEL_VERSION
from cohort.pipeline.models.train import FEATURE_COLUMNS, build_scored_feature_table
from cohort.pipeline.registry import load_model_artifact
from cohort.settings import get_settings
from cohort.store.queue_store import QueueStore


def main() -> None:
    settings = get_settings()
    _patients, features = build_scored_feature_table()

    version_dir = Path(settings.registry_dir) / DEPLOYED_MODEL_VERSION
    pipeline, metadata = load_model_artifact(version_dir)

    x = features[FEATURE_COLUMNS]
    scores = pipeline.predict_proba(x)[:, 1]

    queue_store = QueueStore(Path(settings.queue_store_path))
    enqueued = 0
    for patient_id, score in zip(features["PATIENT_ID"], scores, strict=True):
        if score >= metadata.threshold:
            queue_store.enqueue_case(patient_id, float(score), "high")
            enqueued += 1

    print(f"Enqueued {enqueued:,} of {len(features):,} patients (threshold {metadata.threshold})")


if __name__ == "__main__":
    main()
