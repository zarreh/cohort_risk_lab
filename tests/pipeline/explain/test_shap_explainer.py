import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from cohort.pipeline.explain.shap_explainer import (
    EXPLAINABLE_FEATURES,
    compute_feature_attribution,
)
from cohort.pipeline.features.extract import CATEGORICAL_FEATURES

N = 60


def _synthetic_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data: dict[str, object] = {}
    for col in EXPLAINABLE_FEATURES:
        data[col] = rng.normal(size=N)
    for col in CATEGORICAL_FEATURES:
        data[col] = rng.choice(["A", "B"], size=N)
    return pd.DataFrame(data)


def _fit_pipeline(x: pd.DataFrame) -> Pipeline:
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder

    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",
    )
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression())])
    y = (x[EXPLAINABLE_FEATURES[0]] > 0).astype(int)
    pipeline.fit(x, y)
    return pipeline


def test_returns_top_k_contributions_sorted_by_magnitude() -> None:
    x = _synthetic_data()
    pipeline = _fit_pipeline(x)

    contributions = compute_feature_attribution(pipeline, x, x.iloc[[0]], top_k=3)

    assert len(contributions) == 3
    magnitudes = [abs(c.contribution) for c in contributions]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_direction_matches_contribution_sign() -> None:
    x = _synthetic_data()
    pipeline = _fit_pipeline(x)

    contributions = compute_feature_attribution(pipeline, x, x.iloc[[0]], top_k=5)

    for c in contributions:
        expected = "increases_risk" if c.contribution > 0 else "decreases_risk"
        assert c.direction == expected


def test_categorical_features_are_never_explained() -> None:
    x = _synthetic_data()
    pipeline = _fit_pipeline(x)

    contributions = compute_feature_attribution(
        pipeline, x, x.iloc[[0]], top_k=len(EXPLAINABLE_FEATURES)
    )

    explained_names = {c.feature_name for c in contributions}
    assert explained_names.isdisjoint(set(CATEGORICAL_FEATURES))
