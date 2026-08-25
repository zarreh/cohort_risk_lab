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

**Phase 3 complete — the ML half, including the subgroup fairness audit,
works end to end.** On top of Phase 0 (scaffold), Phase 1 (a real
30,000-patient synthetic cohort) and Phase 2 (calibrated, cost-thresholded,
registered models for both label variants): `pipeline/fairness/` computes
per-stratum calibration, TPR, and enrolment rate with Wilson confidence
intervals on the held-out validation set, gated by a minimum-n policy so a
stratum too small to estimate (native American patients: n=25-42 depending
on split) is shown as insufficient rather than given a misleading point
estimate. `make train` now writes `subgroup_audit.csv` next to every
trained model automatically. See
[evidence/fairness-audit.md](docs/evidence/fairness-audit.md) for the
`v1_burden` results — Hawaiian and "other" patients show a materially lower
true-positive rate than white and Asian, visible only because the audit is
per-stratum. No agent yet — see `docs/PLAN.md` for the phase sequence.

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
