"""Assigns each patient a leakage-safe index date and splits their event
history around it.

This is the ML-specific step `data/build_cohort.py` deliberately stops
short of (docs/PLAN.md §Phases, Phase 1 vs Phase 2): a lifetime aggregate
conflates "what we knew" with "what happened next", which is exactly the
mistake that makes a risk model look better offline than it will ever
perform in production. Every feature in `pipeline/features/` is built only
from events strictly before a patient's `INDEX_DATE`; every label in
`pipeline/labels/` is built only from events in the fixed-length window
strictly after it. The two windows never overlap.

Per-patient index dates (rather than one cohort-wide cutoff) are used
because Synthea patients span very different simulated lifespans — a single
global cutoff would silently exclude anyone whose simulated life ended
earlier. Anchoring `INDEX_DATE` to each patient's own last encounter instead
keeps the inclusion criterion about *how much history that patient has*,
which is the actual clinical concept ("has this person been observed long
enough to screen"), not an artifact of when Synthea happened to stop
simulating them.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_FORWARD_WINDOW_DAYS = 180
DEFAULT_MIN_LOOKBACK_DAYS = 365


def compute_index_dates(
    encounters: pd.DataFrame,
    forward_window_days: int = DEFAULT_FORWARD_WINDOW_DAYS,
    min_lookback_days: int = DEFAULT_MIN_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """One row per patient: INDEX_DATE, the lookback/forward window bounds,
    and whether that patient has enough history to be included at all.

    A patient is included only if their observed history extends at least
    `min_lookback_days` before `INDEX_DATE` — screening someone with three
    weeks of records is not a meaningful lookback window, and silently
    scoring them anyway would understate how much data the model actually
    needs to be useful.
    """
    span = encounters.groupby("PATIENT")["START"].agg(["min", "max"])
    span = span.rename(columns={"min": "FIRST_ENCOUNTER_DATE", "max": "LAST_ENCOUNTER_DATE"})

    index_dates = span["LAST_ENCOUNTER_DATE"] - pd.Timedelta(days=forward_window_days)
    lookback_days = (index_dates - span["FIRST_ENCOUNTER_DATE"]).dt.days

    return pd.DataFrame(
        {
            "PATIENT_ID": span.index,
            "INDEX_DATE": index_dates.to_numpy(),
            "FORWARD_WINDOW_END": (index_dates + pd.Timedelta(days=forward_window_days)).to_numpy(),
            "LOOKBACK_DAYS_AVAILABLE": lookback_days.to_numpy(),
            "INCLUDED": (lookback_days >= min_lookback_days).to_numpy(),
        }
    ).reset_index(drop=True)


def split_events(
    events: pd.DataFrame,
    index_dates: pd.DataFrame,
    date_col: str,
    patient_col: str = "PATIENT",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits one event table into (lookback, forward) halves per patient,
    dropping patients not `INCLUDED` and dropping events outside either
    window entirely (an event after `FORWARD_WINDOW_END` is neither a
    feature nor part of the label — including it would be leakage in one
    direction and noise in the other).
    """
    included = index_dates[index_dates["INCLUDED"]]
    merged = events.merge(
        included[["PATIENT_ID", "INDEX_DATE", "FORWARD_WINDOW_END"]],
        left_on=patient_col,
        right_on="PATIENT_ID",
        how="inner",
    )

    lookback_mask = merged[date_col] < merged["INDEX_DATE"]
    # <=, not <, on the upper bound: FORWARD_WINDOW_END is derived from
    # this patient's own LAST_ENCOUNTER_DATE (see compute_index_dates), so a
    # strict "<" would systematically drop every patient's final encounter
    # from their own forward window.
    forward_mask = (merged[date_col] >= merged["INDEX_DATE"]) & (
        merged[date_col] <= merged["FORWARD_WINDOW_END"]
    )

    drop_cols = ["PATIENT_ID", "INDEX_DATE", "FORWARD_WINDOW_END"]
    lookback = merged.loc[lookback_mask].drop(columns=drop_cols).reset_index(drop=True)
    forward = merged.loc[forward_mask].drop(columns=drop_cols).reset_index(drop=True)
    return lookback, forward
