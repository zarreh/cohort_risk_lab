"""Wilson score confidence intervals for proportions.

Used everywhere the subgroup audit reports a rate (TPR, enrolment rate) for
a stratum — a plain point estimate for a stratum of a few dozen patients
invites a reader to trust a number that hasn't earned it. The Wilson
interval is preferred over the normal (Wald) approximation because it stays
sensible at small n and at proportions near 0 or 1, both of which happen
constantly in the smallest strata this audit reports (docs/PLAN.md's
`min_n` policy, D-A12-5).
"""

from __future__ import annotations

from scipy.stats import norm


def wilson_confidence_interval(
    successes: int, n: int, confidence: float = 0.95
) -> tuple[float, float]:
    """Returns (lower, upper) for the given confidence level. `n == 0`
    returns `(0.0, 1.0)` — total uncertainty, not a division-by-zero error,
    since the caller (the min-n policy) is what decides whether a stratum
    this small should be reported at all."""
    if n == 0:
        return 0.0, 1.0

    z = norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    denominator = 1 + z**2 / n
    center = p_hat + z**2 / (2 * n)
    spread = z * ((p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) ** 0.5)

    lower = (center - spread) / denominator
    upper = (center + spread) / denominator
    return max(0.0, lower), min(1.0, upper)
