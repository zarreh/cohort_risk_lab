"""Loads the deployed model's own prediction for one patient — the single
place `risk_score` and `risk_tier` enter `CaseReviewState`, and the reason
neither field can ever be written by an LLM node in this graph (D-A12-1).

Deterministic, not an agent step: "don't spend an LLM call on a decision
an `if` can make" (UT wk13's deterministic-supervisor pattern, carried over
from A2's `check_plan.py`). Scoring a patient against a trained model is
arithmetic, not judgement.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from cohort.graph.state import CaseReviewState
from cohort.pipeline.explain.shap_explainer import compute_feature_attribution
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import load_model_artifact
from cohort.schemas.case_brief import Driver

HIGH_RISK_TIER = "high"
LOW_RISK_TIER = "low"


def build_load_case_node(
    model_version_dir: Path, feature_table: pd.DataFrame
) -> Callable[[CaseReviewState], dict[str, object]]:
    pipeline, metadata = load_model_artifact(model_version_dir)
    indexed_features = feature_table.set_index("PATIENT_ID")

    def load_case_node(state: CaseReviewState) -> dict[str, object]:
        patient_id = state["patient_id"]
        if patient_id not in indexed_features.index:
            raise ValueError(f"Unknown patient_id {patient_id!r} — not in the scored cohort")

        patient_row = indexed_features.loc[[patient_id], FEATURE_COLUMNS]
        risk_score = float(pipeline.predict_proba(patient_row)[0, 1])
        risk_tier = HIGH_RISK_TIER if risk_score >= metadata.threshold else LOW_RISK_TIER

        contributions = compute_feature_attribution(pipeline, feature_table, patient_row)
        drivers = [
            Driver(feature_name=c.feature_name, contribution=c.contribution, direction=c.direction)
            for c in contributions
        ]

        return {"risk_score": risk_score, "risk_tier": risk_tier, "drivers": drivers}

    return load_case_node
