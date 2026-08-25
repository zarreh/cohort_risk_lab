import numpy as np

from cohort.pipeline.models.compare_labels import _top_quantile_flag


def test_top_quantile_selects_exactly_the_requested_fraction() -> None:
    y_proba = np.linspace(0, 1, 100)
    flagged = _top_quantile_flag(y_proba, quantile=0.20)
    assert flagged.sum() == 20
    assert flagged[-20:].all()  # the top 20 values are the ones flagged


def test_top_quantile_is_a_boolean_array() -> None:
    y_proba = np.array([0.1, 0.9, 0.5])
    flagged = _top_quantile_flag(y_proba, quantile=0.5)
    assert flagged.dtype == bool
