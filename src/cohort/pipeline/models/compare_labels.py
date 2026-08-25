"""The label-choice experiment (PORTFOLIO_PLAN_V3.md §7 A12 pro tier,
promoted into this build per the approved plan): trains `Y_BURDEN` and
`Y_COST` on the identical validation population and compares which
patients each model would flag as high-risk, per race.

**Selection is by a shared top-quantile of each model's predicted
probability, not each model's own deployed cost threshold.** An earlier
version of this comparison used each model's independently
cost-optimised threshold (`pipeline/thresholds/cost_threshold.py`) and
found a large, *uniform* enrolment-rate gap across every race (burden
~60-77%, cost ~37-45%) — real, but uninformative, because it mostly
reflected the two models landing on different global operating points
during threshold search, not the label-choice effect this experiment
exists to isolate. Fixing the selection rate at the same quantile for both
models (matching each label's own `top_k_percent` definition) holds the
programme's enrolment *budget* constant and asks the sharper question
Obermeyer et al. actually asked: given the same number of slots, who gets
one under each label? See D-A12-2 and D-A12-4.

Requires both models to have been trained against the same
`split_train_validation` call — see `pipeline/models/train.py` — so any
divergence found here is attributable to the label choice, not to the two
models having seen different patients.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cohort.pipeline.models.train import FEATURE_COLUMNS, split_train_validation
from cohort.pipeline.registry import load_model_artifact

DEFAULT_SELECTION_QUANTILE = 0.20


def _top_quantile_flag(y_proba: np.ndarray, quantile: float) -> np.ndarray:
    threshold = np.quantile(y_proba, 1 - quantile)
    return np.asarray(y_proba >= threshold)


def compare_label_choice(
    features: pd.DataFrame,
    patients: pd.DataFrame,
    burden_version_dir: Path,
    cost_version_dir: Path,
    selection_quantile: float = DEFAULT_SELECTION_QUANTILE,
) -> pd.DataFrame:
    """One row per race in the shared validation split: each model's
    top-`selection_quantile` enrolment rate, and the percentage-point gap
    between them."""
    _, val_split = split_train_validation(features, patients)
    x_val = val_split[FEATURE_COLUMNS]

    burden_pipeline, _ = load_model_artifact(burden_version_dir)
    cost_pipeline, _ = load_model_artifact(cost_version_dir)

    burden_proba = burden_pipeline.predict_proba(x_val)[:, 1]
    cost_proba = cost_pipeline.predict_proba(x_val)[:, 1]

    result = pd.DataFrame(
        {
            "RACE": val_split["RACE"].to_numpy(),
            "BURDEN_ENROLLED": _top_quantile_flag(burden_proba, selection_quantile),
            "COST_ENROLLED": _top_quantile_flag(cost_proba, selection_quantile),
        }
    )

    summary = result.groupby("RACE").agg(
        N=("RACE", "size"),
        BURDEN_ENROLMENT_RATE=("BURDEN_ENROLLED", "mean"),
        COST_ENROLMENT_RATE=("COST_ENROLLED", "mean"),
    )
    summary["GAP_PERCENTAGE_POINTS"] = (
        summary["COST_ENROLMENT_RATE"] - summary["BURDEN_ENROLMENT_RATE"]
    ) * 100

    return summary.reset_index().sort_values("GAP_PERCENTAGE_POINTS")
