# D-A12-5 — Min-n and confidence-interval policy for subgroup reporting

## Context

Native American patients number 42 in the `v1_cost` validation split (out
of 6,910) — even at a 30,000-patient synthetic cohort, some demographic
strata stay small. A point estimate over 20-40 patients (a TPR of "0.61",
say) invites a reader to trust precision the sample cannot support, and a
naive audit that reports every stratum's raw rate without qualification is
arguably worse than reporting no subgroup breakdown at all, because it
looks rigorous while being misleading.

## Decision

`pipeline/fairness/subgroup_audit.py` applies two rules, together:

1. **`min_n` gate** (default 30): a stratum below this size is still shown
   as a row — `SUFFICIENT_N=False` — but every rate is `NaN` rather than a
   number. The stratum's existence and its size are visible; a spurious
   precise-looking estimate is not.
2. **Wilson score interval** on every rate that *is* reported (TPR,
   enrolment rate), chosen over the normal approximation because it stays
   well-behaved at small n and at proportions near 0 or 1
   (`pipeline/fairness/wilson_ci.py`).

`min_n=30` is a starting default, not a claim of statistical rigor beyond
what it is: a threshold below which this app declines to report a rate at
all, rather than a threshold above which a rate is definitively reliable.
The Wilson interval on every reported rate is what actually communicates
precision (or the lack of it) to a reader.

## Consequences

- The label-choice experiment (Phase 4) and the fairness audit both use
  this same policy — a reader sees confidence intervals get visibly wider
  in exactly the strata (native, hawaiian) that are smallest, which is
  itself part of the honest picture this app is trying to present.
- A stratum can move between "sufficient" and "insufficient" between the
  full-cohort model card table and a smaller ad-hoc slice — e.g. a specific
  age band within a race — and the audit must be re-run per slice rather
  than assuming a stratum that cleared `min_n` overall clears it in every
  cross-tabulation.
