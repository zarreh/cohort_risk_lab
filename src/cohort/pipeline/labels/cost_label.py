"""The realised-cost label: what the deployed algorithm in Obermeyer et al.
(Science, 2019) actually optimised for, while everyone believed it measured
illness (`burden_label.py`).

Built from forward-window encounter and medication costs, then passed
through the same `apply_access_gap` transform the Phase 1 data-profile page
discloses (D-A12-2) — applied here to the *forward-window* total, not the
lifetime aggregate `data/inject_access_gap.py` adjusts, since a label built
from lifetime totals would leak information from before the index date.
"""

from __future__ import annotations

import pandas as pd

from cohort.pipeline.labels.access_gap import AccessGapConfig, apply_access_gap

DEFAULT_TOP_K_PERCENT = 0.20


def build_cost_label(
    included_patient_ids: pd.Series,
    patient_race: pd.DataFrame,
    forward_encounters: pd.DataFrame,
    forward_medications: pd.DataFrame,
    access_gap_config: AccessGapConfig,
    top_k_percent: float = DEFAULT_TOP_K_PERCENT,
) -> pd.DataFrame:
    """One row per included patient: realised forward-window cost, the
    access-gap-adjusted version of it, and whether the adjusted cost lands
    in the top `top_k_percent` of the cohort.
    """
    encounter_cost = forward_encounters.groupby("PATIENT")["TOTAL_CLAIM_COST"].sum()
    medication_cost = forward_medications.groupby("PATIENT")["TOTALCOST"].sum()

    labels = pd.DataFrame({"PATIENT_ID": included_patient_ids})
    labels = labels.merge(encounter_cost, left_on="PATIENT_ID", right_index=True, how="left")
    labels = labels.merge(medication_cost, left_on="PATIENT_ID", right_index=True, how="left")
    labels[["TOTAL_CLAIM_COST", "TOTALCOST"]] = labels[["TOTAL_CLAIM_COST", "TOTALCOST"]].fillna(
        0.0
    )
    labels["REALISED_COST"] = labels["TOTAL_CLAIM_COST"] + labels["TOTALCOST"]
    labels = labels.drop(columns=["TOTAL_CLAIM_COST", "TOTALCOST"])

    labels = labels.merge(patient_race, on="PATIENT_ID", how="left")
    adjusted = apply_access_gap(labels, {**access_gap_config, "adjusted_fields": ["REALISED_COST"]})

    threshold = adjusted["ADJUSTED_REALISED_COST"].quantile(1 - top_k_percent)
    adjusted["Y_COST"] = (adjusted["ADJUSTED_REALISED_COST"] >= threshold).astype("int64")

    return adjusted
