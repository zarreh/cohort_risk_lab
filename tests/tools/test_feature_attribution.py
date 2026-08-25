from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from cohort.pipeline.features.extract import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import ModelMetadata, save_model_artifact
from cohort.tools.feature_attribution import build_feature_attribution_tool

N = 60


def _synthetic_feature_table() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data: dict[str, object] = {"PATIENT_ID": [f"p{i}" for i in range(N)]}
    for col in NUMERIC_FEATURES:
        data[col] = rng.normal(size=N)
    for col in CATEGORICAL_FEATURES:
        data[col] = rng.choice(["A", "B"], size=N)
    for col in BINARY_FEATURES:
        data[col] = rng.choice([True, False], size=N)
    return pd.DataFrame(data)


def _train_and_register(features: pd.DataFrame, tmp_path: Path) -> Path:
    preprocess = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression())])
    x = features[FEATURE_COLUMNS]
    y = (features[NUMERIC_FEATURES[0]] > 0).astype(int)
    pipeline.fit(x, y)

    metadata = ModelMetadata("v_test", "Y_TEST", 0.5, N, 0, {}, FEATURE_COLUMNS)
    return save_model_artifact(pipeline, metadata, tmp_path)


def test_returns_top_features_for_known_patient(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    version_dir = _train_and_register(features, tmp_path)

    tool = build_feature_attribution_tool(version_dir, features)
    result = tool.invoke({"patient_id": "p0"})

    assert len(result) == 5
    assert all(set(r.keys()) == {"feature_name", "contribution", "direction"} for r in result)


def test_unknown_patient_returns_empty_list(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    version_dir = _train_and_register(features, tmp_path)

    tool = build_feature_attribution_tool(version_dir, features)
    result = tool.invoke({"patient_id": "nonexistent"})

    assert result == []
