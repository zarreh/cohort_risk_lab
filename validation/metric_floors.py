"""ML metric floors on a frozen split (docs/PLAN.md, Phase 9).

Fits both `Y_BURDEN` and `Y_COST` — using the exact same
`cohort.pipeline.models.train.fit_and_evaluate` core `make train` uses —
against `validation/fixtures/`, a small, real, seeded sample of the actual
generated Synthea cohort (see `validation/fixtures/build_frozen_fixture.py`
for how it was produced and why a frozen sample, not a live 30k-patient
regeneration, is what CI checks against).

These are regression floors, not aspirational targets: each constant below
was set from the value this frozen split actually produced, with a margin,
not invented in advance. A floor failing means something about the
pipeline changed and should be looked at — not that the model is bad.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV

from cohort.pipeline.models.compare_labels import compare_label_choice_pipelines
from cohort.pipeline.models.train import fit_and_evaluate
from validation.checks import Check

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "deidentified"

MIN_AUROC = 0.60
MAX_ECE = 0.15
TARGET_STRATUM = "black"
# The target stratum must be enrolled *less* under Y_COST than Y_BURDEN.
MAX_LABEL_CHOICE_GAP_PP = -1.0
# At least this many strata must clear DEFAULT_MIN_N in this sample.
MIN_SUFFICIENT_N_STRATA = 3


def _check_model_floors(
    label_name: str, deidentified_dir: Path
) -> tuple[list[Check], CalibratedClassifierCV, pd.DataFrame, pd.DataFrame]:
    pipeline, metadata, subgroup_audit, features, patients = fit_and_evaluate(
        label_name, deidentified_dir
    )
    auroc = metadata.metrics["auroc"]
    ece = metadata.metrics["expected_calibration_error"]

    checks = [
        Check(
            f"{label_name}: AUROC >= {MIN_AUROC}",
            auroc >= MIN_AUROC,
            f"got {auroc:.3f}",
        ),
        Check(
            f"{label_name}: expected calibration error <= {MAX_ECE}",
            ece <= MAX_ECE,
            f"got {ece:.3f}",
        ),
    ]

    sufficient = subgroup_audit[subgroup_audit["SUFFICIENT_N"]]
    checks.append(
        Check(
            f"{label_name}: at least {MIN_SUFFICIENT_N_STRATA} strata clear min_n",
            len(sufficient) >= MIN_SUFFICIENT_N_STRATA,
            f"got {len(sufficient)} of {len(subgroup_audit)}",
        )
    )
    # Every sufficient-n row must report real, in-range numbers; every
    # insufficient-n row must be NaN, never a fabricated substitute
    # (D-A12-5) — a validation floor, not just a unit test, because this is
    # exactly the number this whole app promises never to average away.
    insufficient = subgroup_audit[~subgroup_audit["SUFFICIENT_N"]]
    metric_cols = [c for c in subgroup_audit.columns if c not in ("RACE", "N", "SUFFICIENT_N")]
    insufficient_all_nan = (
        bool(insufficient[metric_cols].isna().all(axis=None)) if len(insufficient) else True
    )
    checks.append(
        Check(
            f"{label_name}: insufficient-n strata report NaN, not fabricated numbers",
            insufficient_all_nan,
            f"{len(insufficient)} insufficient-n row(s)",
        )
    )

    return checks, pipeline, features, patients


def check_metric_floors(fixture_dir: Path = FIXTURE_DIR) -> list[Check]:
    checks: list[Check] = []

    burden_checks, burden_pipeline, burden_features, burden_patients = _check_model_floors(
        "Y_BURDEN", fixture_dir
    )
    cost_checks, cost_pipeline, _, _ = _check_model_floors("Y_COST", fixture_dir)
    checks += burden_checks + cost_checks

    comparison = compare_label_choice_pipelines(
        burden_features, burden_patients, burden_pipeline, cost_pipeline
    )
    target_row = comparison[comparison["RACE"] == TARGET_STRATUM]
    if target_row.empty:
        checks.append(
            Check(
                f"label-choice: {TARGET_STRATUM} stratum present in comparison",
                False,
                "stratum missing from the frozen split's validation population",
            )
        )
    else:
        gap = float(target_row["GAP_PERCENTAGE_POINTS"].iloc[0])
        checks.append(
            Check(
                f"label-choice: {TARGET_STRATUM} gap <= {MAX_LABEL_CHOICE_GAP_PP}pp "
                "(the injected access gap must still show up)",
                gap <= MAX_LABEL_CHOICE_GAP_PP,
                f"got {gap:+.1f}pp",
            )
        )

    return checks


def main() -> int:
    checks = check_metric_floors()
    failed = [c for c in checks if not c.passed]
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name} ({check.detail})")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} metric floors passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
