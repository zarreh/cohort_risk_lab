"""The access-gap mechanism, shared between the Phase 1 data-profile
disclosure (`data/inject_access_gap.py`, operating on lifetime aggregates)
and the label builders here (operating on forward-window aggregates).

Kept as one function so there is exactly one place that implements
D-A12-2 — the injected, disclosed access gap that makes the label-choice
experiment demonstrate something instead of showing a null result. See
`docs/architecture/decisions/D-A12-2-injected-access-gap.md`.
"""

from __future__ import annotations

from typing import TypedDict

import pandas as pd


class AccessGapConfig(TypedDict):
    target_column: str
    target_value: str
    access_reduction_factor: float
    adjusted_fields: list[str]


def apply_access_gap(df: pd.DataFrame, config: AccessGapConfig) -> pd.DataFrame:
    """Scales the configured fields down by `access_reduction_factor` for
    rows in the target stratum, leaving every other row and every other
    column untouched. Adds `ACCESS_GAP_AFFECTED` and one `ADJUSTED_<field>`
    column per adjusted field; the originals are preserved for comparison.
    """
    target_column = config["target_column"]
    target_value = config["target_value"]
    factor = config["access_reduction_factor"]

    result = df.copy()
    affected = result[target_column] == target_value
    result["ACCESS_GAP_AFFECTED"] = affected

    for field in config["adjusted_fields"]:
        adjusted_col = f"ADJUSTED_{field}"
        result[adjusted_col] = result[field].astype("float64")
        result.loc[affected, adjusted_col] = result.loc[affected, field].astype("float64") * factor

    return result
