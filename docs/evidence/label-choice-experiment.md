# The label-choice experiment ★

> The most consequential bug in the most widely deployed clinical algorithm
> in America was not in the model. It was in the label — it predicted cost
> and everyone read it as illness.

This is A12's one clickable artifact: two models, trained on the identical
patient population with the identical features (race and ethnicity excluded
from both, [D-A12-4](../architecture/decisions/D-A12-4-illness-burden-proxy.md)),
differing only in which label they were trained to predict. One reproduces
the failure Obermeyer et al. (*Science*, 2019) documented in a real,
deployed care-management algorithm.

## Disclosure

The divergence below depends on an access gap **injected deliberately, with
a published, seeded parameter** — Synthea has no such disparity built in,
so demonstrating this mechanism on synthetic data requires constructing it.
See [D-A12-2](../architecture/decisions/D-A12-2-injected-access-gap.md) and
`data/access_gap.config.json` for the exact factor. The claim being made is
**"the subgroup audit catches an access gap of this shape,"** not that this
app discovered a real-world disparity.

## The two models

| | `v1_burden` | `v1_cost` |
|---|---|---|
| Label | Count of new conditions in the forward window | Realised forward-window cost, access-gap-adjusted |
| What it represents | What a care-management model *should* predict | What the real deployed algorithm actually optimised |
| AUROC | 0.750 | 0.852 |
| Features | Identical — see the model cards. No race, no ethnicity. |

Notice the cost model scores *better* on its own metric (AUROC 0.852 vs.
0.750) — cost is easier to predict from utilisation history than illness
is from diagnosis codes. This is not a coincidence: it is a large part of
why cost became the convenient, wrong label to optimise for in the first
place.

## The divergence

`pipeline/models/compare_labels.py` selects the top 20% of the shared
validation population by each model's own predicted probability (a fixed
selection budget, not each model's independently-optimised deployment
threshold — see the module docstring for why that distinction matters) and
compares who gets selected, by race:

| Race | N | Burden-model enrolment | Cost-model enrolment | Gap |
|---|---|---|---|---|
| native | 30 | 26.7% | 20.0% | -6.7pp *(n below the audit's min-n threshold — noisy)* |
| **black** | **563** | **22.0%** | **16.3%** | **-5.7pp** |
| hawaiian | 75 | 26.7% | 22.7% | -4.0pp |
| asian | 440 | 23.2% | 20.5% | -2.7pp |
| other | 78 | 14.1% | 11.5% | -2.6pp |
| white | 5,593 | 19.5% | 20.5% | +1.0pp |

Black patients — the stratum sized well enough to trust — show a gap
**2-3x larger** than any other minority group, and white patients show
essentially none. **Neither model was given race as an input feature.**
The gap comes entirely from the access-gap-suppressed utilisation history
correlating with race in this synthetic cohort, exactly mirroring how the
real deployed algorithm produced a racially disparate outcome without race
ever appearing in its feature set.

## Why this took two attempts to get right

The first version of this experiment suppressed cost only in the
*forward-window label* (`Y_COST` itself), leaving the *lookback-window*
features the model actually trains on untouched. The result showed a large
enrolment-rate gap, but it was **uniform across every race** — a symptom of
comparing two independently threshold-optimised models, not of the label
choice. Digging in further: with race excluded from the feature set and no
other feature correlated with the injected gap, the model had no signal to
learn from and could only fit noise. The fix — applying the same access-gap
factor to a patient's lookback utilisation too, not just their forward-
window outcome — is documented in
[D-A12-2](../architecture/decisions/D-A12-2-injected-access-gap.md).
