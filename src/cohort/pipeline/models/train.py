"""Trains, calibrates, thresholds, and registers the care-management risk
model. Runnable via `make train`.

Default label is `Y_BURDEN` — the label a responsibly built care-management
model should use (docs/architecture/decisions D-A12-4 note). Passing
`--label Y_COST` trains the label-choice experiment's second model
(Phase 4) instead; the two runs land in separate registry versions so both
exist on disk at once for the divergence comparison.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from cohort.pipeline.calibration.reliability import expected_calibration_error
from cohort.pipeline.cards.model_card import generate_model_card
from cohort.pipeline.features.extract import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_table,
)
from cohort.pipeline.features.preprocess import build_preprocessor
from cohort.pipeline.labels.burden_label import build_burden_label
from cohort.pipeline.labels.cost_label import build_cost_label
from cohort.pipeline.registry import ModelMetadata, save_model_artifact
from cohort.pipeline.splits import compute_index_dates, split_events
from cohort.pipeline.thresholds.cost_threshold import CostMatrix, optimize_threshold
from cohort.settings import get_settings

DEIDENTIFIED_DIR = Path("data/interim/deidentified")
ACCESS_GAP_CONFIG_PATH = Path("data/access_gap.config.json")
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES

# Missing a patient who would have benefited from enrolment is judged worse
# than enrolling someone who didn't need it — see pipeline/thresholds/cost_threshold.py.
DEFAULT_COST_MATRIX = CostMatrix(cost_false_negative=5.0, cost_false_positive=1.0)


def _load_split_data() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    patients = pd.read_parquet(DEIDENTIFIED_DIR / "patients.parquet").rename(
        columns={"Id": "PATIENT_ID"}
    )
    encounters = pd.read_parquet(DEIDENTIFIED_DIR / "encounters.parquet")
    conditions = pd.read_parquet(DEIDENTIFIED_DIR / "conditions.parquet")
    medications = pd.read_parquet(DEIDENTIFIED_DIR / "medications.parquet")

    index_dates = compute_index_dates(encounters)
    lookback_enc, forward_enc = split_events(encounters, index_dates, date_col="START")
    lookback_cond, forward_cond = split_events(conditions, index_dates, date_col="START")
    lookback_med, forward_med = split_events(medications, index_dates, date_col="START")

    features = build_feature_table(patients, index_dates, lookback_cond, lookback_enc, lookback_med)
    included_ids = index_dates.loc[index_dates["INCLUDED"], "PATIENT_ID"]

    return patients, features, included_ids, forward_enc, forward_cond, forward_med


def _build_label(
    label_name: str,
    patients: pd.DataFrame,
    included_ids: pd.Series,
    forward_cond: pd.DataFrame,
    forward_enc: pd.DataFrame,
    forward_med: pd.DataFrame,
) -> pd.DataFrame:
    if label_name == "Y_BURDEN":
        labels = build_burden_label(included_ids, forward_cond)
        return labels[["PATIENT_ID", "Y_BURDEN"]].rename(columns={"Y_BURDEN": "Y"})
    if label_name == "Y_COST":
        config = json.loads(ACCESS_GAP_CONFIG_PATH.read_text())
        patient_race = patients[["PATIENT_ID", "RACE"]]
        labels = build_cost_label(included_ids, patient_race, forward_enc, forward_med, config)
        return labels[["PATIENT_ID", "Y_COST"]].rename(columns={"Y_COST": "Y"})
    raise ValueError(f"unknown label {label_name!r}")


def train(label_name: str, version: str) -> Path:
    patients, features, included_ids, forward_enc, forward_cond, forward_med = _load_split_data()
    labels = _build_label(
        label_name, patients, included_ids, forward_cond, forward_enc, forward_med
    )

    data = features.merge(labels, on="PATIENT_ID")
    x = data[FEATURE_COLUMNS]
    y = data["Y"].to_numpy()

    x_train, x_val, y_train, y_val = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    base_pipeline = Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            ("classifier", HistGradientBoostingClassifier(random_state=42)),
        ]
    )
    # Isotonic calibration is fit only inside CalibratedClassifierCV's own
    # internal CV folds, so the validation set below is untouched by fitting
    # of any kind — it exists purely to report honest, held-out metrics.
    calibrated = CalibratedClassifierCV(base_pipeline, method="isotonic", cv=5)
    calibrated.fit(x_train, y_train)

    y_val_proba = calibrated.predict_proba(x_val)[:, 1]

    metrics = {
        "auroc": float(roc_auc_score(y_val, y_val_proba)),
        "average_precision": float(average_precision_score(y_val, y_val_proba)),
        "brier_score": float(brier_score_loss(y_val, y_val_proba)),
        "expected_calibration_error": expected_calibration_error(y_val, y_val_proba),
    }
    threshold = optimize_threshold(y_val, y_val_proba, DEFAULT_COST_MATRIX)

    metadata = ModelMetadata(
        version=version,
        label_name=label_name,
        threshold=threshold,
        n_train=len(x_train),
        n_validation=len(x_val),
        metrics=metrics,
        feature_names=FEATURE_COLUMNS,
    )

    registry_dir = Path(get_settings().registry_dir)
    version_dir = save_model_artifact(calibrated, metadata, registry_dir)
    (version_dir / "model_card.md").write_text(generate_model_card(metadata))

    print(
        f"Trained {version} on {label_name}: AUROC={metrics['auroc']:.3f}, "
        f"ECE={metrics['expected_calibration_error']:.3f}, "
        f"threshold={threshold:.3f} -> {version_dir}"
    )
    return version_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="Y_BURDEN", choices=["Y_BURDEN", "Y_COST"])
    parser.add_argument("--version", default=None)
    args = parser.parse_args()
    version = args.version or f"v1_{args.label.lower().removeprefix('y_')}"
    train(args.label, version)


if __name__ == "__main__":
    main()
