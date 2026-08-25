# A12 — Cohort Risk & Review Lab

> The model decides. The agent explains. The human approves. And the
> fairness number is reported per subgroup, not in aggregate.

Portfolio app **A12** (`PORTFOLIO_PLAN_V3.md` §7). Healthcare — population
health / care management, Pillar 2. Target URL: `cohort.zarreh.ai` (not yet
deployed — see Status below).

Over a synthetic Synthea population, a calibrated risk model stratifies
patients for enrolment in a care-management programme. A subgroup audit
reports calibration and true-positive-rate parity across age, sex, race and
insurance strata. Flagged patients land in a clinician review queue where an
agent assembles the case — drivers, corroborating evidence, gaps — but never
assigns the tier and never enrols anyone. Its one clickable artifact
reproduces the **Obermeyer et al. (Science, 2019)** label-choice failure:
training the same model on *cost* versus *illness burden* and showing the
enrolment rate diverge by race.

## Status

**Phase 4 complete — the label-choice experiment, A12's one clickable
artifact, works end to end.** `pipeline/models/compare_labels.py` trains
`Y_BURDEN` and `Y_COST` on the identical validation population (neither
sees race as a feature) and compares each model's own top-20% selection by
race. Result: Black patients are enrolled 5.7 percentage points less often
under the cost-trained model than the burden-trained one — 2-3x the gap
seen for any other minority stratum, White patients show none — reproducing
the Obermeyer et al. (*Science*, 2019) mechanism on synthetic data. See
[evidence/label-choice-experiment.md](docs/evidence/label-choice-experiment.md).

Getting this right took two attempts: the first version suppressed cost
only in the label, leaving the model's lookback features untouched and
with no signal to learn from (verified directly — lookback cost showed
$147.5K vs. $151.9K for Black vs. White, no gap at all) and producing a
uniform, uninformative gap across every race instead. Fixed by applying the
same access-gap factor to a patient's lookback utilisation too, matching
how a real access barrier would actually show up in history —
[D-A12-2](docs/architecture/decisions/D-A12-2-injected-access-gap.md).

On top of Phase 3's subgroup fairness audit (per-stratum calibration, TPR,
and enrolment rate with Wilson CIs, gated by a minimum-n policy), Phase 2's
calibrated cost-thresholded registered models, Phase 1's real 30,000-patient
synthetic cohort, and Phase 0's scaffold. No agent yet — see `docs/PLAN.md`
for the phase sequence.

This will be a research prototype built entirely on synthetic Synthea data.
It is **not** a medical device, does not diagnose, and does not screen for
disease — see `docs/regulatory-basis.md` once it exists.

## Running it

```bash
uv sync --extra dev
cp .env.example .env
make test
make dev               # http://localhost:8000/healthz
```

## Layout

| Path | Purpose |
|---|---|
| `docs/` | MkDocs + Material site — architecture, ADRs, evidence, regulatory basis |
| `docs/PLAN.md` | The build plan — phases, architecture, decisions, risks |
| `src/cohort/pipeline/` | The model half — leakage-safe features, calibration, thresholds, fairness audit. No LangChain import may appear here (enforced by import-linter). |
| `src/cohort/graph/` | The agent half — the evidence agent and case-brief review flow |
| `data/` | Synthea generation, de-identification, cohort build, access-gap injection |
| `validation/` | ML metric floors + canonical brief scenarios (`make validate`) |
| `frontend/` | Next.js UI |
| `tests/` | Backend test suite |
