"""Generates the model card from a trained run's actual metadata — never
hand-written, so it cannot go stale relative to the model it describes
(PORTFOLIO_PLAN_V3.md §9.4, the same discipline `docs/generate_plots.py`
follows for charts).
"""

from __future__ import annotations

from cohort.pipeline.registry import ModelMetadata

LABEL_DESCRIPTIONS = {
    "Y_BURDEN": (
        "Illness burden: count of new conditions recorded in the forward "
        "window. What a care-management model should predict."
    ),
    "Y_COST": (
        "Realised cost: forward-window encounter and medication spend, "
        "access-gap-adjusted. What Obermeyer et al. (Science, 2019) found "
        "a widely deployed algorithm was actually optimising for."
    ),
}


def generate_model_card(metadata: ModelMetadata) -> str:
    label_description = LABEL_DESCRIPTIONS.get(metadata.label_name, metadata.label_name)
    metrics_rows = "\n".join(
        f"| {name} | {value:.4f} |" for name, value in metadata.metrics.items()
    )
    features_list = "\n".join(f"- {name}" for name in metadata.feature_names)

    return f"""# Model card — {metadata.version}

## Label

`{metadata.label_name}` — {label_description}

## Training data

- {metadata.n_train:,} patients in training
- {metadata.n_validation:,} patients in validation
- Synthetic Synthea cohort, Massachusetts, seed committed in `data/synthea.config.json`

## Deployed threshold

`{metadata.threshold:.4f}` — chosen by cost-based optimisation
(`pipeline/thresholds/cost_threshold.py`), not a default 0.5 cutoff.

## Validation metrics

| Metric | Value |
|---|---|
{metrics_rows}

## Features

RACE and ETHNICITY are deliberately excluded as model inputs — see
`docs/architecture/decisions` D-A12-4. The audit uses them as the
stratification key, not the model.

{features_list}

## Known limitations

- This model has never seen real patient data and must never be deployed
  against any. See `docs/regulatory-basis.md`.
- Some demographic strata (e.g. Native American patients) have small n even
  at 30,000 patients — see the subgroup audit's confidence intervals rather
  than treating any single stratum's point estimate as precise.
- Patients with under one year of lookback history were excluded from
  training and scoring entirely (`pipeline/splits.py`), not silently scored
  on insufficient data.
"""
