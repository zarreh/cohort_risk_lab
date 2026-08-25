"""Versioned save/load for a trained model artifact: the fitted pipeline,
its deployed threshold, and the metadata a model card is generated from.

One directory per version (`<registry_dir>/<version>/`), never overwritten
in place — a reviewer comparing the label-choice experiment's two models
(Phase 4) needs both to still exist on disk simultaneously.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline


@dataclass
class ModelMetadata:
    version: str
    label_name: str
    threshold: float
    n_train: int
    n_validation: int
    metrics: dict[str, float]
    feature_names: list[str] = field(default_factory=list)


def save_model_artifact(pipeline: Pipeline, metadata: ModelMetadata, registry_dir: Path) -> Path:
    version_dir = registry_dir / metadata.version
    version_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, version_dir / "pipeline.joblib")
    (version_dir / "metadata.json").write_text(json.dumps(asdict(metadata), indent=2))

    return version_dir


def load_model_artifact(version_dir: Path) -> tuple[Pipeline, ModelMetadata]:
    pipeline = joblib.load(version_dir / "pipeline.joblib")
    raw_metadata = json.loads((version_dir / "metadata.json").read_text())
    return pipeline, ModelMetadata(**raw_metadata)
