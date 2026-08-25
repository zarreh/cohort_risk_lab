import numpy as np
import pandas as pd

from cohort.pipeline.features.extract import BINARY_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES
from cohort.pipeline.features.preprocess import build_preprocessor


def _feature_table(n: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    frame = pd.DataFrame({col: rng.normal(size=n) for col in NUMERIC_FEATURES})
    missing_mask = rng.random(n) < 0.2
    frame.loc[missing_mask, NUMERIC_FEATURES[0]] = np.nan
    for col in CATEGORICAL_FEATURES:
        frame[col] = rng.choice(["A", "B", None], size=n)
    for col in BINARY_FEATURES:
        frame[col] = rng.choice([True, False], size=n)
    return frame


def test_preprocessor_produces_no_nan_output() -> None:
    preprocessor = build_preprocessor()
    transformed = preprocessor.fit_transform(_feature_table())
    assert not np.isnan(transformed).any()


def test_preprocessor_is_unfit_until_called() -> None:
    from sklearn.exceptions import NotFittedError

    preprocessor = build_preprocessor()
    try:
        preprocessor.transform(_feature_table())
        raised = False
    except NotFittedError:
        raised = True
    assert raised


def test_preprocessor_fit_on_train_transforms_unseen_categories_without_error() -> None:
    preprocessor = build_preprocessor()
    train = _feature_table()
    preprocessor.fit(train)

    test = _feature_table()
    test[CATEGORICAL_FEATURES[0]] = "UNSEEN_CATEGORY"
    transformed = preprocessor.transform(test)
    assert not np.isnan(transformed).any()
