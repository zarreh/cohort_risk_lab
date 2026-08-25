import pandas as pd

from cohort.pipeline.labels.access_gap import AccessGapConfig, apply_access_gap

CONFIG: AccessGapConfig = {
    "target_column": "RACE",
    "target_value": "black",
    "access_reduction_factor": 0.5,
    "adjusted_fields": ["ENCOUNTER_COUNT", "TOTAL_CLAIM_COST"],
}


def _cohort() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PATIENT_ID": ["p1", "p2", "p3"],
            "RACE": ["black", "white", "black"],
            "ACTIVE_CONDITION_COUNT": [3, 3, 3],
            "ENCOUNTER_COUNT": [10, 10, 10],
            "TOTAL_CLAIM_COST": [1000.0, 1000.0, 1000.0],
        }
    )


def test_target_stratum_is_scaled_down() -> None:
    result = apply_access_gap(_cohort(), CONFIG)
    black_rows = result[result["RACE"] == "black"]
    assert (black_rows["ADJUSTED_ENCOUNTER_COUNT"] == 5.0).all()
    assert (black_rows["ADJUSTED_TOTAL_CLAIM_COST"] == 500.0).all()


def test_non_target_stratum_is_unchanged() -> None:
    result = apply_access_gap(_cohort(), CONFIG)
    white_rows = result[result["RACE"] == "white"]
    assert (white_rows["ADJUSTED_ENCOUNTER_COUNT"] == white_rows["ENCOUNTER_COUNT"]).all()
    assert (white_rows["ADJUSTED_TOTAL_CLAIM_COST"] == white_rows["TOTAL_CLAIM_COST"]).all()


def test_illness_burden_field_is_never_touched() -> None:
    result = apply_access_gap(_cohort(), CONFIG)
    assert "ADJUSTED_ACTIVE_CONDITION_COUNT" not in result.columns
    assert (result["ACTIVE_CONDITION_COUNT"] == 3).all()


def test_affected_flag_matches_target_stratum() -> None:
    result = apply_access_gap(_cohort(), CONFIG)
    assert result.set_index("PATIENT_ID")["ACCESS_GAP_AFFECTED"].to_dict() == {
        "p1": True,
        "p2": False,
        "p3": True,
    }
