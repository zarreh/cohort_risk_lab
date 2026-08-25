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

**Phase 7 complete — a working FastAPI app with persistence,
server-sent-event streaming, and a real SQLite-backed langgraph
checkpointer**, verified end to end against the live HTTP API (not just
unit tests):

```
curl localhost:8000/queue?status=pending   # 19,409 real flagged patients
curl localhost:8000/queue/{patient_id}      # a real case detail
curl -X POST localhost:8000/queue/{id}/start  # fails exactly at the OpenAI
                                               # credential check — confirmed
                                               # via the actual server log
```

`store/queue_store.py` persists every review case and its node-by-node
events — the same replay-from-store discipline A2's `run_store.py` uses,
adapted for a graph that pauses at `interrupt()` instead of running to
completion in one pass (`api/run_executor.py`'s `start_review` stops the
moment the graph interrupts; `resume_review` is the separate entrypoint a
clinician's decision continues). `api/main.py`'s lifespan opens a real
`AsyncSqliteSaver` at startup, so an interrupted review survives a server
restart, not just an in-process pause.

`data/populate_queue.py` batch-scores the whole cohort with the deployed
model and enqueues everyone above threshold — separated from the
interactive API so starting the server never blocks on rescoring 30,000+
patients. Also caught a real bug in passing: `tests/api/` route tests
proved 404/409/422 error paths work correctly before ever touching a live
graph.

On top of Phase 6's agent and D-A12-1 enforcement, Phase 5's tools and
store, Phase 4's label-choice experiment, Phase 3's fairness audit, Phase
2's calibrated models, Phase 1's cohort, and Phase 0's scaffold. Next: the
Next.js frontend (Phase 8). See `docs/PLAN.md` for the phase sequence.

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
