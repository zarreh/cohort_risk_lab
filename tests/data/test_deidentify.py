import pandas as pd

from data.deidentify import (
    MAX_REPORTABLE_AGE_YEARS,
    _patient_offset_days,
    _shift_dates,
)


def test_patient_offset_is_deterministic_and_bounded() -> None:
    offset_a = _patient_offset_days("patient-1", seed=42)
    offset_b = _patient_offset_days("patient-1", seed=42)
    assert offset_a == offset_b
    assert -365 <= offset_a <= 365


def test_different_patients_get_different_offsets() -> None:
    offset_a = _patient_offset_days("patient-1", seed=42)
    offset_b = _patient_offset_days("patient-2", seed=42)
    assert offset_a != offset_b


def test_shift_dates_preserves_intervals_within_a_patient() -> None:
    dates = pd.Series(["2020-01-01", "2020-06-01"])
    offsets = pd.Series([10, 10])
    shifted = _shift_dates(dates, offsets)
    original_gap = (
        pd.to_datetime(dates.iloc[1], utc=True) - pd.to_datetime(dates.iloc[0], utc=True)
    ).days
    shifted_gap = (shifted.iloc[1] - shifted.iloc[0]).days
    assert shifted_gap == original_gap


def test_age_cap_constant_matches_safe_harbor() -> None:
    assert MAX_REPORTABLE_AGE_YEARS == 90
