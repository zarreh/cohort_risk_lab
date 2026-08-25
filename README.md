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

**Phase 6 complete — the evidence agent, the case-review graph, and D-A12-1
("the LLM is not the risk model") structurally enforced, not asserted.**
`graph/nodes/load_case.py` scores each patient from the deployed model
before any LLM runs; `schemas/case_brief.py`'s `CaseBrief` has no field to
hold a decision; `guardrails/no_decision_guard.py` checks the brief's two
free-text fields for decision language and `verify_brief` routes a
violation back for revision (up to `MAX_REVISIONS`) rather than letting it
through; and the actual decision comes only from a real `interrupt()` /
`Command(resume=...)` cycle, verified against the live langgraph
checkpointer runtime, not mocked. See
[D-A12-1](docs/architecture/decisions/D-A12-1-llm-is-not-the-risk-model.md)
for all four controls and why none of them depend on prompt wording.

No OpenAI API key is available in this build environment, so the two
LLM-backed pieces (the evidence agent's tool-calling loop, the brief-writer
chain) are verified structurally — the graph compiles to the exact node
shape the plan calls for, `load_case` runs for real against a trained
model, and every deterministic node (routing, the guard, the HITL
interrupt/resume cycle) is tested against fake doubles or the real
langgraph runtime — but not against a live model response. The graph fails
exactly at the network call, confirmed directly, not assumed.

On top of Phase 5's tools and store, Phase 4's label-choice experiment,
Phase 3's fairness audit, Phase 2's calibrated models, Phase 1's cohort,
and Phase 0's scaffold. Next: API, persistence, and observability
(Phase 7). See `docs/PLAN.md` for the phase sequence.

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
