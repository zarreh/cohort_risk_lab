"""Regenerates every chart under docs/evidence/ from the actual built cohort
— never hand-drawn (PORTFOLIO_PLAN_V3.md §9.4). `make docs-assets` runs this
and CI fails if the committed charts drift from what it produces, so a
chart can never quietly drift from the data it claims to describe.

Emits a *-light.svg / *-dark.svg pair per chart, selected in the rendered
docs via Material's #only-light / #only-dark image suffixes.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

REPO_ROOT = Path(__file__).resolve().parent.parent
COHORT_PATH = REPO_ROOT / "data" / "cohort" / "cohort.parquet"
STYLE_PATH = REPO_ROOT / "docs" / "assets" / "plot_style.mplstyle"
OUT_DIR = REPO_ROOT / "docs" / "evidence" / "assets"

# Pinned, not today(): the age chart must not change just because a day passed.
AGE_REFERENCE_DATE = pd.Timestamp("2026-08-25", tz="UTC")

DARK_OVERRIDES = {
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#0d1117",
    "savefig.facecolor": "#0d1117",
    "text.color": "#e6edf3",
    "axes.labelcolor": "#e6edf3",
    "axes.edgecolor": "#8b949e",
    "xtick.color": "#e6edf3",
    "ytick.color": "#e6edf3",
    "grid.color": "#8b949e",
}


def _save_pair(fig: Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f"{name}-light.svg", metadata={"Date": None})
    for ax in fig.axes:
        ax.set_facecolor(DARK_OVERRIDES["axes.facecolor"])
    fig.patch.set_facecolor(DARK_OVERRIDES["figure.facecolor"])
    for ax in fig.axes:
        ax.title.set_color(DARK_OVERRIDES["text.color"])
        ax.xaxis.label.set_color(DARK_OVERRIDES["axes.labelcolor"])
        ax.yaxis.label.set_color(DARK_OVERRIDES["axes.labelcolor"])
        ax.tick_params(colors=DARK_OVERRIDES["xtick.color"])
        for spine in ax.spines.values():
            spine.set_edgecolor(DARK_OVERRIDES["axes.edgecolor"])
    fig.savefig(
        OUT_DIR / f"{name}-dark.svg",
        facecolor=DARK_OVERRIDES["savefig.facecolor"],
        metadata={"Date": None},
    )
    plt.close(fig)


def plot_race_distribution(cohort: pd.DataFrame) -> None:
    counts = cohort["RACE"].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots()
    ax.barh(counts.index, counts.to_numpy())
    ax.set_title("Cohort by race")
    ax.set_xlabel("patients")
    for i, value in enumerate(counts.to_numpy()):
        ax.text(float(value), i, f" {value:,}", va="center", fontsize=9)
    _save_pair(fig, "race-distribution")


def plot_age_distribution(cohort: pd.DataFrame) -> None:
    birthdate = pd.to_datetime(cohort["BIRTHDATE"], utc=True)
    age_years = (AGE_REFERENCE_DATE - birthdate).dt.days / 365.25
    fig, ax = plt.subplots()
    ax.hist(age_years.clip(upper=90), bins=30)
    ax.set_title("Cohort age distribution")
    ax.set_xlabel("age (years, capped at 90 per Safe Harbor)")
    ax.set_ylabel("patients")
    _save_pair(fig, "age-distribution")


def plot_condition_burden(cohort: pd.DataFrame) -> None:
    fig, ax = plt.subplots()
    ax.hist(
        cohort["ACTIVE_CONDITION_COUNT"],
        bins=range(0, int(cohort["ACTIVE_CONDITION_COUNT"].max()) + 2),
    )
    ax.set_title("Active condition count (illness burden proxy)")
    ax.set_xlabel("active conditions")
    ax.set_ylabel("patients")
    _save_pair(fig, "condition-burden-distribution")


def main() -> None:
    if not COHORT_PATH.exists():
        print(f"No cohort at {COHORT_PATH} yet — run `make data` first. Skipping plot generation.")
        return

    plt.style.use(STYLE_PATH)
    plt.rcParams["svg.hashsalt"] = "cohort-risk-lab"
    plt.rcParams["axes.prop_cycle"] = plt.cycler(
        color=["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2"]
    )
    cohort = pd.read_parquet(COHORT_PATH)

    plot_race_distribution(cohort)
    plot_age_distribution(cohort)
    plot_condition_burden(cohort)
    print(f"Wrote charts to {OUT_DIR}")


if __name__ == "__main__":
    main()
