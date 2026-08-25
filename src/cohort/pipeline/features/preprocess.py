"""The statistical half of feature preparation: imputation and encoding.

Kept separate from `extract.py` on purpose. Extraction only reads
lookback-window events, so it cannot leak future information no matter when
it runs. Imputation is different — a median or a most-frequent category
computed over the *whole* dataset leaks test-set statistics into training
(the exact defect this app's docs call out in the source
`Case_Study_DiabetesRisk_Prediction.ipynb`, which imputes before the
train/test split). `build_preprocessor()` returns an unfit `ColumnTransformer`
so the caller can `fit` it inside each cross-validation fold and never
outside one.
"""

from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from cohort.pipeline.features.extract import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


def _to_float(values: np.ndarray) -> np.ndarray:
    """A named, module-level function rather than a lambda: `ColumnTransformer`
    is fit inside `CalibratedClassifierCV` and then persisted with joblib
    (`pipeline/registry.py`), and joblib's pickling can't serialise a lambda
    closure — it needs an importable name."""
    return np.asarray(values, dtype=float)


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    # SimpleImputer rejects bool dtype outright, so cast to float first
    # (True/False -> 1.0/0.0) — extract.py never leaves these missing in
    # practice, but this stays a real, independently correct pipeline stage
    # rather than relying on that upstream guarantee.
    binary_pipeline = Pipeline(
        steps=[
            ("to_float", FunctionTransformer(_to_float)),
            ("impute", SimpleImputer(strategy="constant", fill_value=0.0)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("binary", binary_pipeline, BINARY_FEATURES),
        ]
    )
