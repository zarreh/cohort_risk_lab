# D-A12-6 — Shared-code extraction debt

## Context

`PORTFOLIO_PLAN_V3.md` §8 extracts shared packages (X2 `zarreh-agentkit`, X3
`@zarreh/agent-ui`, X5 `zarreh-docs-theme`) only after a **second** working
implementation exists, and never designs one from a single instance. A12 is
that second implementation — but A2 (`trade_sureillance_agent`) was built
first out of the plan's original sequence, so no package has been extracted
yet at all.

## Decision

A12 copies and adapts proven patterns from A2 directly into its own source
tree rather than waiting to extract packages first:

- `settings.py`, `observability.py` — copied near-verbatim (env-prefix and
  project name changed).
- `api/rate_limit.py`, `api/middleware.py` — copied verbatim; both are
  already framework-level, not app-level.
- The §9.3 repo layout and its import-linter contracts — copied and extended
  with one new contract (`pipeline` must never import `langchain`/`langgraph`,
  D-A12-1) that A2 has no equivalent of, since A2 has no ML pipeline half.
- The MkDocs site config and CI/CD workflow shape — copied and adapted.
- The frontend `PrototypeBanner` pattern — copied; `RunConsole`,
  `TraceTimeline`, `EvidencePanel`, `CostMeter` will be copied in Phase 8
  once there is a graph to render.

`zarreh-mlkit` (X4) has no prior instance at all — per §16 it is *born* in
`src/cohort/pipeline/`, and A8 (Reliability Copilot) becomes its second
consumer later, at which point extraction is warranted by the same rule.

## Consequences

- Real duplication exists between A2 and A12 today (settings shape,
  middleware, rate limiting, docs config). This is deliberate debt, not an
  oversight.
- The debt is paid down once a **third** repo needs the same code — at that
  point X2/X3/X5 extract from three concrete instances instead of two,
  which is a stronger basis for the abstraction than extracting after two.
- Nothing about A12's own correctness depends on the debt being paid down;
  it is purely a portfolio-wide maintenance cost, tracked here rather than
  hidden.

## Update (2026-08-27) — the backend half is paid down

A3 (`clinical_care_navigator`) became the third repo. `zarreh-agentkit`
v0.2.0 now carries `settings`, `observability` (incl. `build_tracing_callbacks`,
independently reimplemented identically in A2/A3/A12), `api.middleware`,
`api.rate_limit`, `guardrails.budget`, `guardrails.projection`, and an
`evals` runner shell. A12's `settings.py`, `observability.py`,
`api/middleware.py`, `api/rate_limit.py`, and `run_executor.py`'s tracing
callback now wrap the kit instead of duplicating it; `guardrails/phi_projection.py`
wraps `zarreh_agentkit.guardrails.projection.project_fields`, keeping only
its own `TOOL_FIELD_ALLOWLIST` local. Verified: `make lint`/`typecheck`/`imports`/`test`
(120/120) and `make validate` (18/18) all green afterward.

Still local by design, not debt: `src/cohort/pipeline/` (the ML half — still
the only instance of the proto-`zarreh-mlkit`/X4 shape; A8 is its second
consumer) and `validation/` (the Track-B-style harness, a different shape
from the agentic `evals` runner). The docs/CI/frontend duplication this ADR
also named is unaffected by this update — MkDocs/CI extraction is X5's
concern, not X2's.
