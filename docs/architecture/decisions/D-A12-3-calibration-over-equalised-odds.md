# D-A12-3 — Calibration over equalised odds

## Context

Two properties are commonly asked for from a fair risk model:

- **Calibration**: among patients the model scores at probability *p*, a
  fraction *p* should actually be positive — in every stratum, not just on
  average.
- **Equalised odds**: true-positive and false-positive rates should be
  equal across strata.

Kleinberg, Mullainathan & Raghavan (2016) and Chouldechova (2017) proved
that when base rates differ across strata — which they do here, and do in
essentially every real clinical population — a model **cannot satisfy both
properties simultaneously**, except in the degenerate case of a perfect
predictor. This is not a limitation of any particular modelling technique;
it is a property of arithmetic once base rates diverge.

## Decision

This app optimises for **calibration** and reports the resulting TPR gaps
across strata as the disclosed cost of that choice, rather than either
(a) claiming to have satisfied both properties, or (b) picking equalised
odds and hiding the resulting miscalibration.

`pipeline/models/train.py` calibrates with isotonic regression
(`CalibratedClassifierCV`), and `pipeline/fairness/subgroup_audit.py`
reports **both** calibration-in-the-large/ECE and TPR with a Wilson
interval, per stratum — so a reader sees the trade-off directly rather than
being told it doesn't exist.

## Consequences

- A stratum with a low base rate can show a lower TPR than a
  high-base-rate stratum even under a perfectly calibrated model. This is
  expected, not a bug, and the model card and audit table say so.
- Naming the impossibility result explicitly, rather than asserting the
  model is "fair," is itself the credibility move (PORTFOLIO_PLAN_V3.md §7
  A12: "Naming an impossibility result is a stronger signal than claiming
  to have solved it").
- Calibration was chosen over equalised odds because the downstream
  decision this model feeds (a clinician reviewing a probability) depends
  on that probability meaning the same thing regardless of which patient it
  is attached to — an uncalibrated-but-equalised-odds score would mislead
  every clinician equally, which is a worse failure mode for this
  particular use case than an odds gap a per-stratum audit can surface and
  a clinician can be told about directly.
