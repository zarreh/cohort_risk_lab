"""The illness-burden label: what a care-management algorithm *should* be
predicting, per Obermeyer et al. (Science, 2019) — the thing everyone
assumed the deployed model was optimising for, when it was actually
optimising for cost (`cost_label.py`).

Deliberately built from forward-window *conditions only*, with no cost or
utilisation signal anywhere in it — mixing the two would make the
label-choice experiment (Phase 4) meaningless, since the whole point is
that these two labels diverge under an access gap that affects utilisation
but not underlying illness.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_TOP_K_PERCENT = 0.20


def build_burden_label(
    included_patient_ids: pd.Series,
    forward_conditions: pd.DataFrame,
    top_k_percent: float = DEFAULT_TOP_K_PERCENT,
) -> pd.DataFrame:
    """One row per included patient: how many new conditions were recorded
    in their forward window (0 for anyone with none), and whether that
    count lands in the top `top_k_percent` of the cohort.
    """
    burden_counts = forward_conditions.groupby("PATIENT").size().rename("ILLNESS_BURDEN_SCORE")

    labels = pd.DataFrame({"PATIENT_ID": included_patient_ids})
    labels = labels.merge(burden_counts, left_on="PATIENT_ID", right_index=True, how="left")
    labels["ILLNESS_BURDEN_SCORE"] = labels["ILLNESS_BURDEN_SCORE"].fillna(0).astype("int64")

    threshold = labels["ILLNESS_BURDEN_SCORE"].quantile(1 - top_k_percent)
    labels["Y_BURDEN"] = (labels["ILLNESS_BURDEN_SCORE"] >= threshold).astype("int64")

    return labels
