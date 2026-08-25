import pandas as pd
import pytest

from cohort.pipeline.models.train import _build_label


def test_burden_label_routes_to_burden_builder() -> None:
    included = pd.Series(["p1", "p2"], name="PATIENT_ID")
    forward_cond = pd.DataFrame({"PATIENT": ["p1", "p1"]})
    labels = _build_label(
        "Y_BURDEN", pd.DataFrame(), included, forward_cond, pd.DataFrame(), pd.DataFrame()
    )
    assert set(labels.columns) == {"PATIENT_ID", "Y"}
    assert len(labels) == 2


def test_unknown_label_raises() -> None:
    with pytest.raises(ValueError, match="unknown label"):
        _build_label(
            "Y_NONSENSE",
            pd.DataFrame(),
            pd.Series([], name="PATIENT_ID"),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
