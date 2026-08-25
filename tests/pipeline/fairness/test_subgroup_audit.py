import numpy as np
import pandas as pd

from cohort.pipeline.fairness.subgroup_audit import compute_subgroup_metrics


def test_small_stratum_gets_nan_metrics_not_dropped() -> None:
    y_true = np.array([1, 0, 1, 0, 1])
    y_proba = np.array([0.8, 0.2, 0.7, 0.3, 0.6])
    strata = pd.Series(["rare", "common", "common", "common", "common"])

    result = compute_subgroup_metrics(y_true, y_proba, threshold=0.5, strata=strata, min_n=2)
    rare_row = result[result["STRATUM"] == "rare"].iloc[0]

    assert rare_row["N"] == 1
    assert not rare_row["SUFFICIENT_N"]
    assert pd.isna(rare_row["TPR"])


def test_sufficient_stratum_reports_all_metrics() -> None:
    rng = np.random.default_rng(0)
    n = 100
    y_proba = rng.uniform(0, 1, size=n)
    y_true = (rng.uniform(0, 1, size=n) < y_proba).astype(int)
    strata = pd.Series(["group_a"] * n)

    result = compute_subgroup_metrics(y_true, y_proba, threshold=0.5, strata=strata, min_n=30)
    row = result.iloc[0]

    assert row["SUFFICIENT_N"]
    assert not pd.isna(row["TPR"])
    assert row["TPR_CI_LOWER"] <= row["TPR"] <= row["TPR_CI_UPPER"]
    assert row["ENROLMENT_RATE_CI_LOWER"] <= row["ENROLMENT_RATE"] <= row["ENROLMENT_RATE_CI_UPPER"]


def test_every_stratum_appears_even_when_all_below_min_n() -> None:
    y_true = np.array([1, 0, 1, 0])
    y_proba = np.array([0.6, 0.4, 0.6, 0.4])
    strata = pd.Series(["a", "a", "b", "b"])

    result = compute_subgroup_metrics(y_true, y_proba, threshold=0.5, strata=strata, min_n=10)
    assert set(result["STRATUM"]) == {"a", "b"}
    assert (~result["SUFFICIENT_N"]).all()


def test_worse_calibrated_stratum_shows_larger_gap() -> None:
    n = 200
    y_proba = np.concatenate([np.full(n, 0.9), np.full(n, 0.9)])
    y_true = np.concatenate([np.ones(n), np.zeros(n)])  # second group: predicted 0.9, actual 0
    strata = pd.Series(["well_calibrated"] * n + ["overconfident"] * n)

    result = compute_subgroup_metrics(y_true, y_proba, threshold=0.5, strata=strata, min_n=10)
    indexed = result.set_index("STRATUM")["CALIBRATION_IN_THE_LARGE"]
    well = float(indexed["well_calibrated"])
    over = float(indexed["overconfident"])
    assert abs(over) > abs(well)
