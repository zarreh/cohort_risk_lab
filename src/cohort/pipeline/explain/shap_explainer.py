"""SHAP feature attribution for one patient's prediction, with a stable
schema the agent layer consumes directly (`tools/feature_attribution.py`).

Explains only `NUMERIC_FEATURES + BINARY_FEATURES` — the continuous and
condition-flag features a clinician actually reads a case brief for.
`CATEGORICAL_FEATURES` (gender, marital status) are held fixed at the
patient's own value rather than varied, which sidesteps a real, verified
issue: SHAP's default tabular masker fails outright on a background sample
containing mixed string/numeric columns (`TypeError` inside
`np.isclose`), and mixing bool/float columns into one array without an
explicit cast produces `dtype=object`, which fails the same way one level
deeper. Both were hit and fixed here, not anticipated in the abstract.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

from cohort.pipeline.features.extract import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)
from cohort.pipeline.models.train import FEATURE_COLUMNS

EXPLAINABLE_FEATURES = NUMERIC_FEATURES + BINARY_FEATURES
DEFAULT_BACKGROUND_SIZE = 30
DEFAULT_MAX_EVALS = 500


@dataclass(frozen=True)
class FeatureContribution:
    feature_name: str
    contribution: float
    direction: str  # "increases_risk" | "decreases_risk"


def compute_feature_attribution(
    pipeline: Pipeline,
    background: pd.DataFrame,
    patient_row: pd.DataFrame,
    top_k: int = 5,
) -> list[FeatureContribution]:
    """`background` and `patient_row` must both have every column in
    `FEATURE_COLUMNS`. Returns the `top_k` largest-magnitude contributions
    to this patient's predicted probability, most important first.
    """
    fixed_categorical = {col: patient_row.iloc[0][col] for col in CATEGORICAL_FEATURES}

    def predict_fn(explainable_values: np.ndarray) -> np.ndarray:
        frame = pd.DataFrame(explainable_values, columns=EXPLAINABLE_FEATURES)
        for column, value in fixed_categorical.items():
            frame[column] = value
        proba: np.ndarray = pipeline.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
        return proba

    background_array = (
        background[EXPLAINABLE_FEATURES]
        .astype(float)
        .sample(n=min(DEFAULT_BACKGROUND_SIZE, len(background)), random_state=42)
        .to_numpy()
    )
    row_array = patient_row[EXPLAINABLE_FEATURES].astype(float).to_numpy()

    explainer = shap.Explainer(predict_fn, background_array, feature_names=EXPLAINABLE_FEATURES)
    explanation = explainer(row_array, max_evals=DEFAULT_MAX_EVALS)

    contributions = list(zip(EXPLAINABLE_FEATURES, explanation.values[0], strict=True))
    contributions.sort(key=lambda item: -abs(item[1]))

    return [
        FeatureContribution(
            feature_name=name,
            contribution=float(value),
            direction="increases_risk" if value > 0 else "decreases_risk",
        )
        for name, value in contributions[:top_k]
    ]
