from cohort.pipeline.fairness.wilson_ci import wilson_confidence_interval


def test_zero_n_returns_total_uncertainty() -> None:
    assert wilson_confidence_interval(0, 0) == (0.0, 1.0)


def test_interval_contains_point_estimate() -> None:
    lower, upper = wilson_confidence_interval(50, 100)
    assert lower < 0.5 < upper


def test_smaller_n_gives_wider_interval_at_same_rate() -> None:
    small_lower, small_upper = wilson_confidence_interval(5, 10)
    large_lower, large_upper = wilson_confidence_interval(500, 1000)
    assert (small_upper - small_lower) > (large_upper - large_lower)


def test_bounds_stay_within_zero_and_one() -> None:
    lower, upper = wilson_confidence_interval(0, 5)
    assert 0.0 <= lower <= upper <= 1.0
    lower, upper = wilson_confidence_interval(5, 5)
    assert 0.0 <= lower <= upper <= 1.0
