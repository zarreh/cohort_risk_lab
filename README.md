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

**Phase 5 complete — the evidence tools and the runtime store they read
from.** `data/build_cohort_store.py` builds `data/cohort.db` (5.6GB, batched
Parquet reads to stay under this machine's 14GB RAM — the naive
whole-table-in-memory version OOM-killed twice on the 16M-row observations
table, confirmed via `dmesg`) from the de-identified cohort data.
`cohort.store.CohortStore` gives sub-millisecond, typed, read-only access to
it. Five tools sit on top — `patient_encounters`, `patient_labs`,
`care_gap_lookup`, `missing_data_check`, `feature_attribution` (real SHAP
values from the deployed model, ~8s per call) — every one narrow, typed,
and filtered through `guardrails/phi_projection.py`'s HIPAA
minimum-necessary allowlist, never a query the model could construct freely
([D-A12-7](docs/architecture/decisions/D-A12-7-typed-tools-not-text-to-sql.md),
rejecting the source notebook's text-to-SQL-plus-keyword-blocklist
approach).

Fixing the tools/pipeline import direction surfaced a genuine layering bug:
`feature_attribution` needs the trained model, which means `tools` must be
allowed to depend on `pipeline` — the import-linter contract had them the
wrong way round from Phase 0, when no tool needed pipeline internals yet.
Reordered to `api -> graph -> {tools,guardrails} -> pipeline -> schemas`.

On top of Phase 4's label-choice experiment, Phase 3's fairness audit,
Phase 2's calibrated models, Phase 1's cohort, and Phase 0's scaffold. Next:
the evidence agent and review-queue graph (Phase 6), where D-A12-1 ("the
LLM is not the risk model") gets structurally enforced. See `docs/PLAN.md`
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
