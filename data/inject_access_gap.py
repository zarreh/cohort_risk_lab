"""Injects a deliberate, disclosed, seeded access gap into realised
utilisation and spend for one demographic stratum, at equal illness burden.

This is not a bug being simulated by accident: Synthea generates cost from
utilisation with no differential access by race, so training on cost vs.
illness-burden labels over an unmodified cohort shows little divergence — a
null result dressed as a finding. The mechanism below is what makes the
label-choice experiment (`pipeline/labels/`, Phase 4) actually demonstrate
the failure mode Obermeyer et al. (Science, 2019) documented, instead of
merely claiming to.

Every parameter is in the committed `data/access_gap.config.json`. Every
page in this app that shows the resulting divergence must disclose this
file — see docs/architecture/decisions (D-A12-2). The claim being
demonstrated is that the subgroup audit *catches* an access gap, not that
this app discovered one in the wild.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "data" / "access_gap.config.json"
COHORT_PATH = REPO_ROOT / "data" / "cohort" / "cohort.parquet"
SAMPLE_DIR = REPO_ROOT / "data" / "sample"
SAMPLE_SIZE = 50


def inject_access_gap(cohort: pd.DataFrame, config: dict[str, object]) -> pd.DataFrame:
    target_column = str(config["target_column"])
    target_value = config["target_value"]
    factor = float(config["access_reduction_factor"])  # type: ignore[arg-type]
    adjusted_fields = list(config["adjusted_fields"])  # type: ignore[call-overload]

    result = cohort.copy()
    affected = result[target_column] == target_value
    result["ACCESS_GAP_AFFECTED"] = affected

    for field in adjusted_fields:
        adjusted_col = f"ADJUSTED_{field}"
        result[adjusted_col] = result[field].astype("float64")
        result.loc[affected, adjusted_col] = result.loc[affected, field].astype("float64") * factor

    return result


def _write_sample(cohort: pd.DataFrame) -> None:
    """The only cohort artifact this repo commits (docs/PLAN.md §Phases,
    Phase 1) — deidentified, age-capped, with the final access-gap columns
    this whole pipeline produces, and with no absolute dates by
    construction (see data/deidentify.py). Dates are dropped entirely as an
    extra margin: this table's purpose is to show the shape of the data,
    not to let anyone reconstruct a patient's timeline."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    date_cols = [c for c in cohort.columns if "DATE" in c]
    sample = cohort.drop(columns=date_cols).sample(n=SAMPLE_SIZE, random_state=42)
    sample_path = SAMPLE_DIR / "cohort_sample.parquet"
    sample.to_parquet(sample_path, index=False)
    print(f"sample: {len(sample)} patients -> {sample_path}")


def main() -> None:
    config: dict[str, object] = json.loads(CONFIG_PATH.read_text())
    cohort = pd.read_parquet(COHORT_PATH)

    adjusted = inject_access_gap(cohort, config)
    adjusted.to_parquet(COHORT_PATH, index=False)

    n_affected = int(adjusted["ACCESS_GAP_AFFECTED"].sum())
    print(
        f"Access gap applied to {n_affected:,} of {len(adjusted):,} patients "
        f"({config['target_column']}={config['target_value']!r}, "
        f"factor={config['access_reduction_factor']}) -> {COHORT_PATH}"
    )

    _write_sample(adjusted)


if __name__ == "__main__":
    main()
