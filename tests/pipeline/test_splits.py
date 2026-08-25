import pandas as pd

from cohort.pipeline.splits import compute_index_dates, split_events


def _encounters() -> pd.DataFrame:
    # p1: 800-day span -> included (>= 365 lookback after 180-day forward window)
    # p2: 200-day span -> excluded (too short)
    return pd.DataFrame(
        {
            "PATIENT": ["p1", "p1", "p1", "p2", "p2"],
            "START": pd.to_datetime(
                [
                    "2020-01-01",
                    "2021-06-01",
                    "2022-03-11",  # p1 span = 800 days
                    "2020-01-01",
                    "2020-07-19",  # p2 span = 200 days
                ],
                utc=True,
            ),
        }
    )


def test_included_flag_reflects_lookback_availability() -> None:
    idx = compute_index_dates(_encounters(), forward_window_days=180, min_lookback_days=365)
    included = idx.set_index("PATIENT_ID")["INCLUDED"].to_dict()
    assert included == {"p1": True, "p2": False}


def test_index_date_is_last_encounter_minus_forward_window() -> None:
    idx = compute_index_dates(_encounters(), forward_window_days=180, min_lookback_days=365)
    p1 = idx.set_index("PATIENT_ID").loc["p1"]
    assert p1["INDEX_DATE"] == pd.Timestamp("2022-03-11", tz="UTC") - pd.Timedelta(days=180)


def test_split_events_excludes_patients_without_enough_lookback() -> None:
    idx = compute_index_dates(_encounters(), forward_window_days=180, min_lookback_days=365)
    lookback, forward = split_events(_encounters(), idx, date_col="START")
    assert set(lookback["PATIENT"]) == {"p1"}
    assert set(forward["PATIENT"]) == {"p1"}


def test_split_events_never_crosses_the_index_date() -> None:
    idx = compute_index_dates(_encounters(), forward_window_days=180, min_lookback_days=365)
    lookback, forward = split_events(_encounters(), idx, date_col="START")
    index_date = idx.set_index("PATIENT_ID").loc["p1", "INDEX_DATE"]
    assert (lookback["START"] < index_date).all()
    assert (forward["START"] >= index_date).all()


def test_split_events_drops_events_past_the_forward_window() -> None:
    # FORWARD_WINDOW_END is always some patient's own LAST_ENCOUNTER_DATE
    # (see compute_index_dates), so no *encounter* row can ever fall past
    # it. A different event table (e.g. lab observations) can, and must be
    # dropped from both halves rather than silently kept in the forward set.
    idx = compute_index_dates(_encounters(), forward_window_days=180, min_lookback_days=365)
    labs = pd.DataFrame(
        {
            "PATIENT": ["p1"],
            "DATE": pd.to_datetime(["2025-01-01"], utc=True),
        }
    )
    lookback, forward = split_events(labs, idx, date_col="DATE")
    assert lookback.empty
    assert forward.empty
