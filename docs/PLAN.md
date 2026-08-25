# A12 — Cohort Risk & Review Lab · Build Plan

**Portfolio ref:** `PORTFOLIO_PLAN_V3.md` §7 (A12), §9 (engineering standard),
§9.3 (repo layout), §9.4 (documentation standard), §10 (frontend),
§16 (Track B — the ML half this app also carries)
**Repo:** `cohort_risk_lab/` · package `cohort` · URL `cohort.zarreh.ai`
**Scope:** `base` + the label-choice experiment, committed. Remaining `pro`
items (threshold explorer, override analytics, drift monitor) deferred.
**Drafted:** 2026-08-25

---

## 0. Framing

A12 is the second app built, immediately after A2, and out of the plan's
stated sequence (§13 originally placed it seventh, after X1-X5 and five other
apps exist). It is being built now because it is the **priority-domain,
Track A ↔ Track B bridge**, and because A2 already proved the template (§9.3
layout, FastAPI + Next.js baseline, CI/CD, MkDocs site) — so A12 reuses that
proof rather than repeating Phase 0's full time-box.

**No shared package exists yet.** X2 (`zarreh-agentkit`), X3 (`@zarreh/agent-ui`),
X4 (`zarreh-mlkit`) and X5 (`zarreh-docs-theme`) are not extracted — the
portfolio rule is that no package is born from a single implementation, and
A12 is only the second repo. Proven patterns (settings, observability,
prompts loader, SSE bridge, import-linter contracts, CI, the React
components) are **copied and adapted from A2**, not imported. The resulting
duplication between A2 and A12 is recorded as extraction debt — see
D-A12-6 — and is exactly the debt X2/X3/X5 pay down once a third app arrives.
X4 (`zarreh-mlkit`) has no prior instance at all; per §16 it is *born* here,
in `src/cohort/pipeline/`, and A8 becomes its second consumer later.

**The one portfolio argument this app makes.** The LLM must not be the risk
model. A calibrated statistical model makes the prediction; an agent explains
it; a clinician decides — and the fairness claim is reported per subgroup,
with confidence intervals, not as a single aggregate number that hides where
the model actually fails.

**The honest-design problem.** Synthea generates cost from utilisation with
no differential access by race, so training on cost vs. illness-burden labels
over unmodified Synthea would show little divergence — a null result dressed
as a finding. The access gap is therefore **injected deliberately, with a
seeded, committed, published parameter** (`data/inject_access_gap.py`), and
every page showing the experiment discloses this. The claim being
demonstrated is that the subgroup audit *catches* the gap, not that the app
discovered it in the wild. See D-A12-2.

---

## 1. Confirmed decisions

| # | Decision |
|---|---|
| 1 | Location: `cohort_risk_lab/`, its own git repo, sibling to `trade_sureillance_agent/` under `~/portfolio_projects/` conventions but created at `~/greatlearning/cohort_risk_lab/` per the user's instruction to build it at the root of the greatlearning folder. |
| 2 | Cohort: Synthea generated fresh at ~30k patients (JDK + Synthea jar, committed seed + config) rather than reusing the existing 1,163-patient JHU week14 extract, whose smallest strata (native n=2, hawaiian n=18) cannot support per-subgroup TPR parity claims. |
| 3 | Scope: full `base` tier plus the label-choice experiment ships in this build. Threshold explorer, override analytics and drift monitor are explicitly deferred `pro` items. |
| 4 | Shared code: build inline, adapted from A2. No X2/X3/X4/X5 extraction before this repo exists. |

---

## 2. Source material

- `agentic_ai_jhu/advanced_agentic_aI /week14/Agentic_AI_Interaction_Embodiment_MS_Risk_Lab.ipynb` — multi-agent risk scoring, adjustable-autonomy policy table, cohort/dashboard framing.
- `agentic_ai_jhu/advanced_agentic_aI /week14/healthcare_hitl_assistant.ipynb` — `interrupt()` HITL pattern, audit-log discipline.
- `Post_Graduate_Program_in_Artificial-Intelligence_Machine_Learning/04_advanced_machine_learning/week_1/practice_exercise/Case_Study_DiabetesRisk_Prediction.ipynb` — calibrated tabular risk modelling, used here mostly as the *negative* example (pre-split imputation is leakage).
- `Post_Graduate_Program_in_Artificial-Intelligence_Machine_Learning/08_model_deployment/` — the serving skeleton this app modernises away from Flask/Streamlit/bare joblib.

## 3. What must NOT be ported

| Source | Rejected | Instead |
|---|---|---|
| `healthcare_hitl_assistant.ipynb` | Text-to-SQL against the patient database, gated by an `UNSAFE_KEYWORDS` string scan that is trivially bypassable. | Typed, read-only tools with Pydantic arg schemas. No generated SQL anywhere (D-A12-7). |
| `..._MS_Risk_Lab.ipynb` | Hand-tuned linear weights presented as a model; MS *diagnosis* framing; agents as bare Python classes; matplotlib "dashboard". | A trained, calibrated, cost-thresholded model. Care-management *enrolment* framing only — never screening, never disease identification. LangGraph nodes. Recharts + generated docs plots. |
| `Case_Study_DiabetesRisk_Prediction.ipynb` | Median imputation before the train/test split (leakage); no calibration; no subgroup analysis. | Imputation inside the CV pipeline; isotonic calibration with reliability diagrams; per-stratum audit with a temporal split. |
| `08_model_deployment/` | Flask, Streamlit, bare `joblib` blobs. | FastAPI, Next.js, a versioned registry with an auto-generated model card. |

**What survives:** the MS lab's adjustable-autonomy policy table (thresholds
as data, owned by the clinical owner) → the review queue's threshold policy;
its patient card → the case brief; the HITL notebook's `interrupt()` +
audit-log discipline → `await_decision` / `record_decision`.

## 4. Architecture

A12 carries both halves of the §9.3 template because it is the bridge:
`pipeline/` (Track B, no LLM import permitted — enforced by import-linter)
and `graph/` (Track A).

### 4.1 Graph (built in Phase 6, once the model and tools exist)

```
load_case → assemble_evidence ⇄ tools → check_missing → draft_brief
          → verify_brief ──(ungrounded)──> assemble_evidence
          → await_decision  [interrupt()]  → record_decision
```

`verify_brief` reuses A2's grounding-loop pattern exactly: each statement in
the brief is scored against recorded tool results, aggregation is
deterministic in the node (never authored by the judge model), and a failed
check routes back to gather more evidence rather than silently rewriting the
brief.

### 4.2 Enforcing "the agent never decides"

1. `CaseBrief` has no risk-tier field and no enrolment field — there is
   nowhere for a decision to go.
2. Every tool is read-only and returns only fields on the `phi_projection`
   minimum-necessary allowlist, enforced in the tool layer.
3. `no_decision_guard` rejects a brief containing enrolment/recommendation
   verbs; the test suite asserts the rejection fires.

### 4.3 Labels (the experiment)

| Label | Definition |
|---|---|
| `y_cost` | Total realised spend over the forward window, top-k% → 1. What the deployed algorithm actually optimised. |
| `y_burden` | Count of active chronic conditions plus uncontrolled clinical markers over the same window, top-k% → 1. What everyone believed it was optimising. |

Identical features, pipeline and threshold policy train two models; the
enrolment-rate divergence by race is the artifact.

### 4.4 Fairness reporting

Per stratum (age band, sex, race, ethnicity, payer class): calibration-in-
the-large and slope, ECE, TPR at the deployed threshold, enrolment rate —
every number with a Wilson confidence interval. Strata below `min_n` render
as "insufficient n", never silently dropped. Calibration is chosen over
equalised odds and that trade-off is stated plainly (D-A12-3).

## 5. Files (§9.3)

```
src/cohort/
├── api/                    # routes/, deps.py, streaming.py, middleware.py, rate_limit.py
├── pipeline/               # splits, features, labels, models, calibration,
│                           #   thresholds, fairness, explain, cards, registry
├── graph/                  # state, builder, edges, policies, nodes/, agents/, chains/
├── tools/                  # feature_attribution, patient_encounters, patient_labs,
│                           #   care_gap_lookup, missing_data_check
├── guardrails/             # phi_projection.py, no_decision_guard.py
├── prompts/ · schemas/ · store/ · settings.py · observability.py
data/                       # generate_synthea.py, deidentify.py, build_cohort.py,
│                           #   inject_access_gap.py, synthea.config (committed), sample/
validation/                 # Track B's evals/: metric floors + canonical brief scenarios
frontend/                   # Next.js 15, components copied from A2
```

## 6. Documentation

Same per-repo MkDocs standard as A2 (§9.4): three audiences, generated
visualisations, CI-gated `--strict` build. `docs/regulatory_basis.md` covers
HIPAA minimum-necessary, FDA CDS guidance, NCQA/HEDIS vocabulary and the
Obermeyer et al. (Science, 2019) finding this app deliberately reproduces on
synthetic, seeded data.

## 7. Phases

| # | Phase | Contents |
|---|---|---|
| 0 | Scaffold + walking skeleton | Repo, quality gates, CI/CD, MkDocs `--strict`, FastAPI `/healthz`, trivial two-node graph, Next.js first paint. |
| 1 | Data *(no LLM)* | JDK + Synthea jar; generate ~30k patients with a committed seed; de-identify (Safe Harbor); build cohort parquet; inject access gap; data-profile charts. Raw CSVs/DB gitignored. |
| 2 | Pipeline | Temporal split, feature transformer, both label builders, estimator, calibration, cost threshold, registry, generated model card. |
| 3 | Subgroup audit | Per-stratum metrics with Wilson CIs, min-n policy, reliability diagrams, calibration-vs-equalised-odds writeup. |
| 4 | Label-choice experiment ★ | Two trained models, enrolment-rate divergence table/chart, injected-mechanism disclosure. |
| 5 | Tools + guardrails | Five typed tools over the cohort store; `phi_projection` allowlist; tool-level tests. |
| 6 | Agent graph | Evidence agent, brief writer, brief verifier (grounding loop), `interrupt()` HITL, decision + override log. |
| 7 | API, persistence, observability | Routes, SSE bridge, SQLite checkpointer, queue/decision stores, structlog, LangSmith callbacks. |
| 8 | Frontend | RunConsole/TraceTimeline/EvidencePanel/CostMeter/PrototypeBanner (copied from A2) + ReviewQueue, CaseBrief, ReliabilityDiagram, SubgroupTable, LabelChoiceExperiment. |
| 9 | Validation harness | `make validate` — ML metric floors + canonical brief scenarios, gates PR CI. |
| 10 | Docs + launch | Regulatory basis, ADRs, evidence pages, README, banner on every page. |

## 8. Decisions to record as ADRs

D-A12-1 the LLM is not the risk model, and how that is structurally enforced
· D-A12-2 the injected access gap, and why disclosing it is stronger than
hiding it · D-A12-3 calibration over equalised odds · D-A12-4 the
illness-burden proxy and its limits · D-A12-5 min-n and confidence-interval
policy for subgroup reporting · D-A12-6 shared-code extraction debt (X2/X3/
X4/X5 deferred; A12 is repo #2) · D-A12-7 typed tools instead of text-to-SQL.

## 9. Out of scope (this build)

Per-subgroup threshold explorer, override analytics, cohort drift monitor
(remaining `pro` items — gated on base being deployed, same discipline A2
followed). Cross-provider model support. Live public deployment (no
infrastructure access while building).

## 10. Risks

| Risk | Mitigation |
|---|---|
| 30k Synthea patients ≈ 10GB+ of CSV | Restrict exported tables via Synthea config; build a compact parquet cohort immediately; gitignore raw output. |
| Small strata persist even at 30k | The min-n policy handles it; stated as a real limitation in the model card, not hidden. |
| No JDK, no Docker-in-WSL today | JDK installed as a Phase 1 step. Docker only matters at deploy; A2 deferred live deployment for the same reason. |
| App spans both Track A and Track B | Phases 2-4 have no LLM at all and are independently verifiable before any agent code exists. |

## 11. Quality gate — conditions to publish `base`

`make lint typecheck imports test` green · `make validate` green (metric
floors + canonical scenarios) · `mkdocs build --strict` green ·
`make docs-assets` produces no diff · manual walk (queue → case brief with no
tier/enrolment field → decision recorded → subgroup audit with CIs →
label-choice experiment with disclosure) completes without error.
