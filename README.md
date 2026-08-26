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

![Homepage](docs/assets/homepage-screenshot.png)

## Status

**Phase 9 complete — a PR-CI validation gate**: `make validate` fits both
models against a committed, real (seeded, stratified-by-race sample of
the actual generated cohort) frozen split and checks AUROC/calibration
floors plus the label-choice gap never regresses to zero, then runs four
hand-authored canonical patients through the real risk-scoring node and
tools — a care gap that must fire, one that must not, a low-risk patient,
and one with no data at all. Wired into CI right after pytest. See
[docs/evidence/validation-harness.md](docs/evidence/validation-harness.md).

**Phase 8: a working full-stack app**, every page verified
against real backend data (not screenshots of mockups):

- `/queue` — the real 19,409-patient review queue, highest risk first
- `/queue/[patientId]` — real case detail, a Start Review button, an
  SSE-driven trace timeline, and the decision form (interrupt/resume via
  the real backend — see Phase 7)
- `/evidence/fairness` — the real subgroup audit table, insufficient-n
  strata rendered as such rather than a misleading number
- `/evidence/label-choice` — the real label-choice divergence chart
  (recharts), narrating the exact -5.7pp Black-patient gap from Phase 4

Verified by starting both servers and reading the actual rendered HTML —
`19,409 pending cases`, `Risk score 1.000`, real per-stratum TPR
percentages, the real -5.7pp gap narrative — not by inspecting component
code in isolation. `CORSMiddleware` (configurable allowed origins, not
`*`) was a real, necessary addition once the browser started making
cross-origin calls from the Next.js dev server to the API.

Playwright is wired (`frontend-e2e`, `docs-screenshots`) with a real
browser installed and passing; the homepage screenshot above is captured
by that same smoke test, per the documentation standard, not hand-taken.

On top of Phase 8's frontend, Phase 7's persistent API, Phase 6's agent and
D-A12-1 enforcement, Phase 5's tools and store, Phase 4's label-choice
experiment, Phase 3's fairness audit, Phase 2's calibrated models, Phase
1's cohort, and Phase 0's scaffold. Next: launch docs (Phase 10). See
`docs/PLAN.md` for the phase sequence.

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
