"""Builds the five tools the evidence agent can call.

One store connection and one feature table, shared across tools rather
than reopened per call — the same discipline A2's tool registry follows.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.tools import StructuredTool

from cohort.store.cohort_store import CohortStore
from cohort.tools.care_gap_lookup import build_care_gap_lookup_tool
from cohort.tools.feature_attribution import build_feature_attribution_tool
from cohort.tools.missing_data_check import build_missing_data_check_tool
from cohort.tools.patient_encounters import build_patient_encounters_tool
from cohort.tools.patient_labs import build_patient_labs_tool


def build_tools(
    store: CohortStore, model_version_dir: Path, feature_table: pd.DataFrame
) -> list[StructuredTool]:
    """Returns all five tools, bound to the given store and deployed
    model version."""
    return [
        build_patient_encounters_tool(store),
        build_patient_labs_tool(store),
        build_care_gap_lookup_tool(store),
        build_missing_data_check_tool(store),
        build_feature_attribution_tool(model_version_dir, feature_table),
    ]
