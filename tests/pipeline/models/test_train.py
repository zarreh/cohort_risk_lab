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


def test_split_is_deterministic_and_label_independent() -> None:
    import pandas as pd

    from cohort.pipeline.models.train import split_train_validation

    features = pd.DataFrame({"PATIENT_ID": [f"p{i}" for i in range(100)]})
    patients = pd.DataFrame(
        {
            "PATIENT_ID": [f"p{i}" for i in range(100)],
            "RACE": (["white"] * 60 + ["black"] * 40),
        }
    )

    train_a, val_a = split_train_validation(features, patients)
    train_b, val_b = split_train_validation(features, patients)

    # Two independent calls (standing in for the two separate `train()`
    # invocations for Y_BURDEN and Y_COST) must land on the identical
    # patient partition, since nothing about the label enters this split.
    assert set(val_a["PATIENT_ID"]) == set(val_b["PATIENT_ID"])
    assert set(train_a["PATIENT_ID"]) == set(train_b["PATIENT_ID"])


def test_lookback_access_gap_suppresses_target_stratum_utilisation() -> None:
    import pandas as pd

    from cohort.pipeline.models.train import (
        LOOKBACK_ACCESS_GAP_FIELDS,
        _apply_lookback_access_gap,
    )

    features = pd.DataFrame(
        {
            "PATIENT_ID": ["p1", "p2"],
            "LOOKBACK_ENCOUNTER_COUNT": [10.0, 10.0],
            "LOOKBACK_TOTAL_CLAIM_COST": [1000.0, 1000.0],
            "LOOKBACK_MEDICATION_COUNT": [5.0, 5.0],
            "LOOKBACK_MEDICATION_TOTAL_COST": [200.0, 200.0],
            "AGE_AT_INDEX": [40.0, 40.0],
        }
    )
    patients = pd.DataFrame({"PATIENT_ID": ["p1", "p2"], "RACE": ["black", "white"]})

    adjusted = _apply_lookback_access_gap(features, patients)

    assert list(adjusted.columns) == list(features.columns)
    indexed = adjusted.set_index("PATIENT_ID")
    for field in LOOKBACK_ACCESS_GAP_FIELDS:
        column = indexed[field]
        p1_value = float(column["p1"])
        p2_value = float(column["p2"])
        assert p1_value < p2_value  # target stratum suppressed
    # non-target, non-adjusted columns must be untouched
    assert (adjusted["AGE_AT_INDEX"] == 40.0).all()
