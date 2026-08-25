"""Read-only tool: why the model scored this patient the way it did.

Loads the deployed model straight from the registry rather than the graph
carrying its own copy — one source of truth for "which model is live," and
a tool this narrow is cheap to keep in sync with whatever `make train`
last produced.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from cohort.pipeline.explain.shap_explainer import compute_feature_attribution
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import load_model_artifact

TOOL_NAME = "feature_attribution"


class FeatureAttributionArgs(BaseModel):
    patient_id: str = Field(description="The patient's de-identified id")


def build_feature_attribution_tool(
    registry_version_dir: Path, feature_table: pd.DataFrame
) -> StructuredTool:
    """`feature_table` is the full cohort's extracted feature table
    (`pipeline/features/extract.py`), used both as the SHAP background
    sample and as the source of the one row being explained — the tool
    itself never re-runs feature extraction per call."""
    pipeline, _ = load_model_artifact(registry_version_dir)
    indexed_features = feature_table.set_index("PATIENT_ID")

    def feature_attribution(patient_id: str) -> list[dict[str, object]]:
        if patient_id not in indexed_features.index:
            return []
        patient_row = indexed_features.loc[[patient_id], FEATURE_COLUMNS]
        contributions = compute_feature_attribution(pipeline, feature_table, patient_row)
        return [
            {
                "feature_name": c.feature_name,
                "contribution": c.contribution,
                "direction": c.direction,
            }
            for c in contributions
        ]

    return StructuredTool.from_function(
        func=feature_attribution,
        name=TOOL_NAME,
        description=(
            "Returns the top features driving this patient's risk score, "
            "with the direction each one pushed the prediction."
        ),
        args_schema=FeatureAttributionArgs,
    )
