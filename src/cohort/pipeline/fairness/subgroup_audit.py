"""Per-stratum calibration and TPR parity — the audit this whole app is
built to make credible (PORTFOLIO_PLAN_V3.md §7 A12: "the fairness number
is reported per subgroup, not in aggregate").

A single aggregate AUC or calibration curve can look excellent while
hiding a model that fails badly for one demographic group — this is
exactly the failure mode Obermeyer et al. (Science, 2019) documented, and
exactly what this function is built to surface instead of hide.

Deliberately reports **both** calibration and TPR, and does not attempt to
equalise both (D-A12-3): calibration and equalised odds cannot both hold
across strata with different base rates (Kleinberg, Mullainathan & Raghavan
2016; Chouldechova 2017). This app names that impossibility rather than
claiming to have solved it, and chooses calibration as the property it
optimises for — see the ADR.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cohort.pipeline.calibration.reliability import expected_calibration_error
from cohort.pipeline.fairness.wilson_ci import wilson_confidence_interval

DEFAULT_MIN_N = 30


def _tpr(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int]:
    """Returns (true_positives, actual_positives) so the caller can compute
    both the rate and its Wilson interval from the same two integers."""
    actual_positive = y_true == 1
    true_positives = int((actual_positive & (y_pred == 1)).sum())
    return true_positives, int(actual_positive.sum())


def compute_subgroup_metrics(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float,
    strata: pd.Series,
    min_n: int = DEFAULT_MIN_N,
) -> pd.DataFrame:
    """One row per distinct value of `strata`: n, whether n clears
    `min_n`, calibration-in-the-large, expected calibration error, TPR at
    `threshold` with its Wilson CI, and the enrolment (flagged) rate with
    its Wilson CI.

    A stratum below `min_n` still gets a row — with `SUFFICIENT_N=False`
    and every rate set to `NaN` — rather than being silently dropped, so a
    reader of the audit table sees that the group exists and was excluded
    from point estimates, not that it was never considered.
    """
    y_pred = (y_proba >= threshold).astype(int)
    frame = pd.DataFrame(
        {"stratum": strata.to_numpy(), "y_true": y_true, "y_proba": y_proba, "y_pred": y_pred}
    )

    rows = []
    for stratum_value, group in frame.groupby("stratum"):
        n = len(group)
        sufficient = n >= min_n

        row: dict[str, object] = {"STRATUM": stratum_value, "N": n, "SUFFICIENT_N": sufficient}

        if sufficient:
            true_positives, actual_positives = _tpr(
                group["y_true"].to_numpy(), group["y_pred"].to_numpy()
            )
            tpr = true_positives / actual_positives if actual_positives > 0 else float("nan")
            tpr_lower, tpr_upper = (
                wilson_confidence_interval(true_positives, actual_positives)
                if actual_positives > 0
                else (float("nan"), float("nan"))
            )

            flagged = int(group["y_pred"].sum())
            enrolment_rate = flagged / n
            enrolment_lower, enrolment_upper = wilson_confidence_interval(flagged, n)

            row.update(
                {
                    "CALIBRATION_IN_THE_LARGE": float(
                        group["y_proba"].mean() - group["y_true"].mean()
                    ),
                    "EXPECTED_CALIBRATION_ERROR": expected_calibration_error(
                        group["y_true"].to_numpy(), group["y_proba"].to_numpy()
                    ),
                    "TPR": tpr,
                    "TPR_CI_LOWER": tpr_lower,
                    "TPR_CI_UPPER": tpr_upper,
                    "ENROLMENT_RATE": enrolment_rate,
                    "ENROLMENT_RATE_CI_LOWER": enrolment_lower,
                    "ENROLMENT_RATE_CI_UPPER": enrolment_upper,
                }
            )
        else:
            for metric in (
                "CALIBRATION_IN_THE_LARGE",
                "EXPECTED_CALIBRATION_ERROR",
                "TPR",
                "TPR_CI_LOWER",
                "TPR_CI_UPPER",
                "ENROLMENT_RATE",
                "ENROLMENT_RATE_CI_LOWER",
                "ENROLMENT_RATE_CI_UPPER",
            ):
                row[metric] = float("nan")

        rows.append(row)

    return pd.DataFrame(rows)
