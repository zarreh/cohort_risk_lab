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
from cohort.pipeline.fairness.subgroup_audit import DEFAULT_MIN_N, compute_subgroup_metrics
from cohort.pipeline.features.extract import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_table,
)
from cohort.pipeline.features.preprocess import build_preprocessor
from cohort.pipeline.labels.access_gap import AccessGapConfig, apply_access_gap
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

# Which lookback-window utilisation features the access gap suppresses —
# see _apply_lookback_access_gap below for why this has to exist at all.
LOOKBACK_ACCESS_GAP_FIELDS = [
    "LOOKBACK_ENCOUNTER_COUNT",
    "LOOKBACK_TOTAL_CLAIM_COST",
    "LOOKBACK_MEDICATION_COUNT",
    "LOOKBACK_MEDICATION_TOTAL_COST",
]


def _apply_lookback_access_gap(features: pd.DataFrame, patients: pd.DataFrame) -> pd.DataFrame:
    """Applies the same D-A12-2 access-gap factor to a patient's *historical*
    utilisation features, not just the forward-window label.

    Without this, the model has no way to reproduce the label-choice
    experiment's effect at all: `cost_label.py` suppresses only the
    forward-window realised cost used to build `Y_COST`, and race is
    (deliberately, D-A12-4) excluded from the model's inputs — so unless a
    patient's *lookback* utilisation also reflects the access barrier, the
    model has zero learnable signal correlated with the label suppression
    and can only fit noise. This mirrors the real mechanism Obermeyer et
    al. describe: a genuine access barrier shows up throughout a patient's
    utilisation history, which is exactly what a real predictive model's
    input features would capture and (without meaning to) learn from — the
    same historical signal is why the real deployed algorithm could
    reproduce the disparity while never being given race directly.
    """
    base_config = json.loads(ACCESS_GAP_CONFIG_PATH.read_text())
    lookback_config: AccessGapConfig = {
        "target_column": base_config["target_column"],
        "target_value": base_config["target_value"],
        "access_reduction_factor": base_config["access_reduction_factor"],
        "adjusted_fields": LOOKBACK_ACCESS_GAP_FIELDS,
    }
    with_race = features.merge(patients[["PATIENT_ID", "RACE"]], on="PATIENT_ID")
    adjusted = apply_access_gap(with_race, lookback_config)

    for field in LOOKBACK_ACCESS_GAP_FIELDS:
        adjusted[field] = adjusted[f"ADJUSTED_{field}"]
    return adjusted[features.columns]


def build_scored_feature_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Loads the deidentified cohort and returns `(patients, features)` —
    the same access-gap-adjusted feature table both training and the
    running API score patients against. Public (not `_`-prefixed) because
    `api/deps.py::get_feature_table` needs the identical table a deployed
    model was trained on; duplicating this loading logic there would risk
    the two silently drifting apart.
    """
    patients = pd.read_parquet(DEIDENTIFIED_DIR / "patients.parquet").rename(
        columns={"Id": "PATIENT_ID"}
    )
    encounters = pd.read_parquet(DEIDENTIFIED_DIR / "encounters.parquet")
    conditions = pd.read_parquet(DEIDENTIFIED_DIR / "conditions.parquet")
    medications = pd.read_parquet(DEIDENTIFIED_DIR / "medications.parquet")

    index_dates = compute_index_dates(encounters)
    lookback_enc, _ = split_events(encounters, index_dates, date_col="START")
    lookback_cond, _ = split_events(conditions, index_dates, date_col="START")
    lookback_med, _ = split_events(medications, index_dates, date_col="START")

    features = build_feature_table(patients, index_dates, lookback_cond, lookback_enc, lookback_med)
    features = _apply_lookback_access_gap(features, patients)
    return patients, features


def _load_split_data() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    patients, features = build_scored_feature_table()

    encounters = pd.read_parquet(DEIDENTIFIED_DIR / "encounters.parquet")
    conditions = pd.read_parquet(DEIDENTIFIED_DIR / "conditions.parquet")
    medications = pd.read_parquet(DEIDENTIFIED_DIR / "medications.parquet")

    index_dates = compute_index_dates(encounters)
    _, forward_enc = split_events(encounters, index_dates, date_col="START")
    _, forward_cond = split_events(conditions, index_dates, date_col="START")
    _, forward_med = split_events(medications, index_dates, date_col="START")

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


def split_train_validation(
    features: pd.DataFrame, patients: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits by patient, independent of which label will be trained.

    Deliberately label-independent (stratified by RACE, not by Y) so that
    `v1_burden` and `v1_cost` — trained in two separate calls to `train()`
    — end up with the *identical* set of held-out patients. The Phase 4
    label-choice experiment compares the two models' predictions on the
    same validation population; if each run picked its own split, an
    observed divergence could just as easily be sampling noise as the
    label-choice effect it's meant to demonstrate.
    """
    with_race = features.merge(patients[["PATIENT_ID", "RACE"]], on="PATIENT_ID")
    train_split, val_split = train_test_split(
        with_race, test_size=0.2, random_state=42, stratify=with_race["RACE"]
    )
    return train_split, val_split


def train(label_name: str, version: str) -> Path:
    patients, features, included_ids, forward_enc, forward_cond, forward_med = _load_split_data()
    labels = _build_label(
        label_name, patients, included_ids, forward_cond, forward_enc, forward_med
    )

    train_split, val_split = split_train_validation(features, patients)
    train_data = train_split.merge(labels, on="PATIENT_ID")
    val_data = val_split.merge(labels, on="PATIENT_ID")

    x_train, y_train = train_data[FEATURE_COLUMNS], train_data["Y"].to_numpy()
    x_val, y_val = val_data[FEATURE_COLUMNS], val_data["Y"].to_numpy()

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

    # Computed on the held-out validation set only — never the training
    # data the model has already fit, and never the whole cohort, either
    # of which would report an overly optimistic (or simply wrong) picture
    # of how the model behaves on data it hasn't seen (PORTFOLIO_PLAN_V3.md
    # §7 A12: "the fairness number is reported per subgroup").
    subgroup_audit = compute_subgroup_metrics(
        y_val, y_val_proba, threshold, val_data["RACE"], min_n=DEFAULT_MIN_N
    )

    registry_dir = Path(get_settings().registry_dir)
    version_dir = save_model_artifact(calibrated, metadata, registry_dir)
    (version_dir / "model_card.md").write_text(generate_model_card(metadata))
    subgroup_audit.to_csv(version_dir / "subgroup_audit.csv", index=False)

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
