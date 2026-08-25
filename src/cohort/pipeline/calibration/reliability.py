"""Reliability (calibration) curves: for a well-calibrated model, patients
the model scores at 0.3 should turn out positive about 30% of the time,
in every bin and — this is what `pipeline/fairness/` (Phase 3) checks —
in every demographic stratum, not just on average.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_reliability_curve(
    y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10
) -> pd.DataFrame:
    """One row per bin of predicted probability: how many patients fell in
    it, their mean predicted probability, and their actual positive rate.
    Bins with zero patients are omitted rather than shown as a misleading
    flat line.
    """
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_index = np.clip(np.digitize(y_proba, bin_edges[1:-1], right=True), 0, n_bins - 1)

    frame = pd.DataFrame({"bin": bin_index, "y_true": y_true, "y_proba": y_proba})
    grouped = frame.groupby("bin").agg(
        MEAN_PREDICTED=("y_proba", "mean"),
        MEAN_ACTUAL=("y_true", "mean"),
        COUNT=("y_true", "size"),
    )
    return grouped.reset_index(drop=True)


def expected_calibration_error(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> float:
    """Weighted average gap between predicted and actual rate across bins —
    a single number summarising the reliability curve above."""
    curve = compute_reliability_curve(y_true, y_proba, n_bins)
    weights = curve["COUNT"] / curve["COUNT"].sum()
    gaps = (curve["MEAN_PREDICTED"] - curve["MEAN_ACTUAL"]).abs()
    return float((weights * gaps).sum())
