import numpy as np

from cohort.pipeline.calibration.reliability import (
    compute_reliability_curve,
    expected_calibration_error,
)


def test_perfectly_calibrated_model_has_zero_ece() -> None:
    rng = np.random.default_rng(42)
    y_proba = rng.uniform(0, 1, size=5000)
    y_true = (rng.uniform(0, 1, size=5000) < y_proba).astype(int)
    ece = expected_calibration_error(y_true, y_proba, n_bins=10)
    assert ece < 0.05


def test_overconfident_model_has_high_ece() -> None:
    y_proba = np.full(1000, 0.9)
    y_true = np.zeros(1000, dtype=int)  # actual rate 0, predicted 0.9
    ece = expected_calibration_error(y_true, y_proba, n_bins=10)
    assert ece > 0.5


def test_empty_bins_are_omitted() -> None:
    y_proba = np.array([0.05, 0.05, 0.95, 0.95])
    y_true = np.array([0, 0, 1, 1])
    curve = compute_reliability_curve(y_true, y_proba, n_bins=10)
    assert len(curve) == 2
    assert curve["COUNT"].sum() == 4
