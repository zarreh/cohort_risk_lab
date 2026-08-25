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
