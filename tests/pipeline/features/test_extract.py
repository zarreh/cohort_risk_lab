import pandas as pd

from cohort.pipeline.features.extract import (
    MAX_REPORTABLE_AGE_YEARS,
    build_feature_table,
)


def _index_dates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PATIENT_ID": ["p1", "p2"],
            "INDEX_DATE": pd.to_datetime(["2022-01-01", "2022-01-01"], utc=True),
            "INCLUDED": [True, True],
        }
    )


def _patients() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PATIENT_ID": ["p1", "p2"],
            "BIRTHDATE": pd.to_datetime(["1990-01-01", "1920-01-01"], utc=True),
            "GENDER": ["F", "M"],
            "MARITAL": ["M", None],
            "INCOME": [50000, 30000],
        }
    )


def test_excluded_patients_are_dropped() -> None:
    index_dates = _index_dates()
    index_dates.loc[1, "INCLUDED"] = False
    features = build_feature_table(
        _patients(),
        index_dates,
        pd.DataFrame(columns=["PATIENT", "STOP", "CODE", "DESCRIPTION"]),
        pd.DataFrame(columns=["PATIENT", "Id", "TOTAL_CLAIM_COST", "ENCOUNTERCLASS"]),
        pd.DataFrame(columns=["PATIENT", "CODE", "TOTALCOST"]),
    )
    assert set(features["PATIENT_ID"]) == {"p1"}


def test_age_is_clipped_at_safe_harbor_boundary() -> None:
    features = build_feature_table(
        _patients(),
        _index_dates(),
        pd.DataFrame(columns=["PATIENT", "STOP", "CODE", "DESCRIPTION"]),
        pd.DataFrame(columns=["PATIENT", "Id", "TOTAL_CLAIM_COST", "ENCOUNTERCLASS"]),
        pd.DataFrame(columns=["PATIENT", "CODE", "TOTALCOST"]),
    )
    # p2 was born in 1920 -> ~102 at index; must clip to the 90 cap, not report it raw.
    p2_age = features.set_index("PATIENT_ID").loc["p2", "AGE_AT_INDEX"]
    assert p2_age == MAX_REPORTABLE_AGE_YEARS


def test_patients_with_no_lookback_events_get_zero_counts_not_missing_columns() -> None:
    features = build_feature_table(
        _patients(),
        _index_dates(),
        pd.DataFrame(columns=["PATIENT", "STOP", "CODE", "DESCRIPTION"]),
        pd.DataFrame(columns=["PATIENT", "Id", "TOTAL_CLAIM_COST", "ENCOUNTERCLASS"]),
        pd.DataFrame(columns=["PATIENT", "CODE", "TOTALCOST"]),
    )
    assert (features["LOOKBACK_ENCOUNTER_COUNT"] == 0).all()
    assert (features["HAS_DIABETES"] == False).all()  # noqa: E712


def test_chronic_condition_flag_is_set_from_description_keyword() -> None:
    conditions = pd.DataFrame(
        {
            "PATIENT": ["p1"],
            "STOP": [None],
            "CODE": [123],
            "DESCRIPTION": ["Type 2 diabetes mellitus (disorder)"],
        }
    )
    features = build_feature_table(
        _patients(),
        _index_dates(),
        conditions,
        pd.DataFrame(columns=["PATIENT", "Id", "TOTAL_CLAIM_COST", "ENCOUNTERCLASS"]),
        pd.DataFrame(columns=["PATIENT", "CODE", "TOTALCOST"]),
    )
    result = features.set_index("PATIENT_ID")
    assert result.loc["p1", "HAS_DIABETES"]
    assert not result.loc["p2", "HAS_DIABETES"]
