# Validation harness

`make validate` (`validation/run.py`) is the PR CI gate: two independent
checks, both run against data committed to this repository, neither
requiring a JDK, a live Synthea run, or an OpenAI key.

## ML metric floors — a frozen split

`validation/fixtures/` is a small, seeded, stratified-by-race sample of the
real 30k-patient Synthea cohort this app trains against — not invented
data. `validation/fixtures/build_frozen_fixture.py` produced it once from
a real `make data` run and the result was committed; regenerating it is a
deliberate, occasional action, not something `make data` or CI ever does.

`validation/metric_floors.py` fits `Y_BURDEN` and `Y_COST` against this
frozen split using the exact same `pipeline.models.train.fit_and_evaluate`
core `make train` uses — the same code path, smaller input — and checks:

- AUROC and expected calibration error for both labels clear a floor.
- At least three race strata clear the fairness audit's `min_n` policy,
  and every stratum below it reports `NaN`, never a fabricated number
  ([D-A12-5](../architecture/decisions/D-A12-5-min-n-confidence-intervals.md)).
- The label-choice experiment's Black-patient enrolment gap
  ([D-A12-2](../architecture/decisions/D-A12-2-injected-access-gap.md)) is
  still negative beyond a floor — the one number this whole app exists to
  demonstrate must not silently regress to zero.

Every floor constant was set from what the frozen split actually produced,
with a margin — a regression guard, not an aspirational target.

## Canonical brief scenarios

Four hand-authored patients exercise the graph's deterministic, non-LLM
parts against known-correct outcomes: a diabetic patient with no glucose
lab (a care gap must fire), a diabetic patient with one on file (no gap),
a low-utilisation patient, and a patient with no recorded history at all
(every evidence category must be reported missing, never silently treated
as normal). `validation/canonical_scenarios.py` runs the real
`load_case` risk-scoring node and the real tools against these patients,
plus `no_decision_guard` against a clean and a decision-language-carrying
brief.

These four are hand-authored, not mined from the real cohort, because a
Synthea-simulated patient who is diagnosed with diabetes is always given a
glucose test in the same run — "diabetic with no glucose lab ever
recorded" does not occur naturally anywhere in the generated data.
Testing the care-gap tool honestly requires a constructed vignette.

What this does *not* cover: the LLM-backed evidence agent and brief writer
themselves, which need a live OpenAI key this build environment doesn't
have. `tests/graph/test_case_review_integration.py` already proves the
graph's control flow — including a real `interrupt()`/resume cycle — with
fake stand-ins for those two nodes; this harness checks scenario-level
correctness of everything around them instead.
