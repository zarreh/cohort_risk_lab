from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from cohort.graph.nodes.load_case import HIGH_RISK_TIER, LOW_RISK_TIER, build_load_case_node
from cohort.graph.state import create_initial_case_review_state
from cohort.pipeline.features.extract import BINARY_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import ModelMetadata, save_model_artifact

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


def _train_and_register(features: pd.DataFrame, threshold: float, tmp_path: Path) -> Path:
    preprocess = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression())])
    x = features[FEATURE_COLUMNS]
    y = (features[NUMERIC_FEATURES[0]] > 0).astype(int)
    pipeline.fit(x, y)

    metadata = ModelMetadata("v_test", "Y_TEST", threshold, N, 0, {}, FEATURE_COLUMNS)
    return save_model_artifact(pipeline, metadata, tmp_path)


def test_unknown_patient_raises(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    version_dir = _train_and_register(features, threshold=0.5, tmp_path=tmp_path)
    node = build_load_case_node(version_dir, features)

    try:
        node(create_initial_case_review_state("nonexistent"))
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_tier_reflects_deployed_threshold(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    # threshold of 0.0 -> everyone with score >= 0.0 (i.e. everyone) is "high"
    version_dir = _train_and_register(features, threshold=0.0, tmp_path=tmp_path)
    node = build_load_case_node(version_dir, features)

    result = node(create_initial_case_review_state("p0"))
    assert result["risk_tier"] == HIGH_RISK_TIER

    # threshold of 1.01 -> nobody clears it
    version_dir_low = _train_and_register(features, threshold=1.01, tmp_path=tmp_path / "b")
    node_low = build_load_case_node(version_dir_low, features)
    result_low = node_low(create_initial_case_review_state("p0"))
    assert result_low["risk_tier"] == LOW_RISK_TIER


def test_returns_five_drivers(tmp_path: Path) -> None:
    features = _synthetic_feature_table()
    version_dir = _train_and_register(features, threshold=0.5, tmp_path=tmp_path)
    node = build_load_case_node(version_dir, features)

    result = node(create_initial_case_review_state("p0"))
    drivers = result["drivers"]
    assert isinstance(drivers, list)
    assert len(drivers) == 5
