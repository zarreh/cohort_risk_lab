# Subgroup fairness audit

Computed by `pipeline/fairness/subgroup_audit.py` on the **held-out
validation set only** — never on data the model was trained on, and never
on the whole cohort, either of which would report a rosier picture than the
model actually earns. `pipeline/models/train.py` runs this automatically
and writes `subgroup_audit.csv` next to every trained model in the
registry.

Every rate carries a Wilson score interval ([D-A12-5](../architecture/decisions/D-A12-5-min-n-confidence-intervals.md)).
A stratum below 30 patients in the validation split is still shown, with
every rate reported as insufficient rather than a misleadingly precise
number.

## `v1_burden` — the deployed model (label: illness burden)

| Stratum | N | TPR | TPR 95% CI | Enrolment rate | Enrolment rate 95% CI |
|---|---|---|---|---|---|
| asian | 437 | 0.826 | [0.732, 0.891] | 0.538 | [0.491, 0.584] |
| black | 564 | 0.791 | [0.713, 0.852] | 0.578 | [0.537, 0.618] |
| hawaiian | 72 | 0.611 | [0.386, 0.797] | 0.431 | [0.323, 0.546] |
| native | 25 | — insufficient n (< 30) — | | | |
| other | 92 | 0.607 | [0.424, 0.764] | 0.478 | [0.379, 0.579] |
| white | 5,589 | 0.797 | [0.774, 0.819] | 0.537 | [0.524, 0.550] |

Hawaiian and "other" show a materially lower TPR than white and asian —
visible *because* the audit is per-stratum, and invisible in an aggregate
AUROC of 0.750. This is the finding the plan calls out directly: "per-
stratum calibration is the thing that actually breaks in production."

## Calibration vs. equalised odds

Per [D-A12-3](../architecture/decisions/D-A12-3-calibration-over-equalised-odds.md),
this model is calibrated (expected calibration error under 0.05 in every
sufficient-n stratum above), not equalised-odds-matched — the two cannot
both hold once base rates differ across strata, and that trade-off is named
here rather than hidden.

*(Regenerated whenever `make train` runs; see `artifacts/registry/<version>/subgroup_audit.csv`
for the machine-readable version and every metric this page summarises.)*
