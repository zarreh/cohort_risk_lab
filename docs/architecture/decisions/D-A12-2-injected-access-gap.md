# D-A12-2 — The injected access gap, disclosed

## Context

The label-choice experiment (Phase 4) is the app's one clickable artifact:
train the same model on *realised cost* vs. *illness burden* and show the
resulting enrolment rate diverge by race — reproducing the mechanism behind
Obermeyer et al. (*Science*, 2019), where a widely deployed care-management
algorithm under-referred Black patients because it optimised cost, not
illness.

Synthea has no such mechanism. It generates realised cost directly from
simulated utilisation, with no differential access by race built in. Training
`y_cost` vs. `y_burden` over an unmodified Synthea cohort would show little or
no divergence — a null result, and reporting it as evidence of anything would
be dishonest.

## Decision

Inject the access gap deliberately, with every parameter in a committed,
version-controlled config: `data/access_gap.config.json`. For the configured
stratum, realised utilisation and spend fields are scaled down by a fixed
factor — **at equal illness burden**, meaning `ACTIVE_CONDITION_COUNT` (the
label-burden proxy) is never touched. See `data/inject_access_gap.py`.

**Applied twice, consistently, using the same config.** The obvious first
attempt — suppressing only the *forward-window* cost used to build `Y_COST`
(`pipeline/labels/cost_label.py`) — turned out to be insufficient on its
own: `pipeline/models/train.py`'s model never sees race as a feature
(D-A12-4), and if the *lookback* utilisation features it does see carry no
trace of the access barrier, the model has no learnable signal to fit and
can only reproduce noise. A quick verification confirmed this directly:
lookback total claim cost for Black vs. White patients was
$147,506 vs. $151,858 — no gap at all — before this fix.

The same factor is therefore also applied to a patient's *lookback-window*
utilisation features (`pipeline/models/train.py::_apply_lookback_access_gap`),
representing the same synthetic reality: a genuine access barrier would show
up throughout a patient's history, not conveniently only in the window being
predicted. This is what lets a model trained without race as an input still
reproduce a race-correlated outcome — mirroring exactly how the real
Obermeyer algorithm worked, and the more interesting, harder-to-dismiss
version of the claim (see D-A12-4).

Every page in this app that shows the label-choice divergence discloses this
mechanism and links to this ADR and to `data/access_gap.config.json`.

## Consequences

- The claim this app demonstrates is **"the subgroup audit catches an access
  gap of this shape"** — not "this app discovered a real-world disparity."
  That is a smaller, more honest claim, and it is the one actually being made.
- Reviewers can inspect the exact factor and reproduce the result.
- If the injected factor is ever set to `1.0` (no-op), the label-choice chart
  should show near-zero divergence — this is itself a useful regression test
  for the experiment's validity (`validation/`, Phase 9).
- Verified end to end: with the factor applied consistently, the
  cost-vs-burden model comparison (`pipeline/models/compare_labels.py`)
  shows Black patients enrolled at a rate 5.7 percentage points lower under
  the cost-trained model than the burden-trained one — 2-3x the gap seen
  for any other minority stratum, and White patients show essentially no
  gap at all (+1.0pp). See `docs/evidence/label-choice-experiment.md`.
