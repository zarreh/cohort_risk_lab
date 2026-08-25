import numpy as np

from cohort.pipeline.thresholds.cost_threshold import CostMatrix, optimize_threshold


def test_expensive_false_negatives_push_threshold_down() -> None:
    y_true = np.array([1, 1, 1, 0, 0, 0])
    y_proba = np.array([0.9, 0.6, 0.3, 0.7, 0.4, 0.1])

    fn_expensive = CostMatrix(cost_false_negative=100.0, cost_false_positive=1.0)
    fp_expensive = CostMatrix(cost_false_negative=1.0, cost_false_positive=100.0)

    threshold_low = optimize_threshold(y_true, y_proba, fn_expensive)
    threshold_high = optimize_threshold(y_true, y_proba, fp_expensive)

    assert threshold_low < threshold_high


def test_threshold_is_within_valid_probability_range() -> None:
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, size=200)
    y_proba = rng.uniform(0, 1, size=200)
    threshold = optimize_threshold(y_true, y_proba, CostMatrix(5.0, 1.0))
    assert 0.0 <= threshold <= 1.0
