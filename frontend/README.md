# Cohort Risk & Review Lab — frontend

Next.js 15 (App Router) + Tailwind v4. HTTP client only — no business logic
here; the FastAPI backend under `../src/cohort/api/` is the only source of
truth (`PORTFOLIO_PLAN_V3.md` §10).

```bash
npm install
npm run dev   # http://localhost:3000 — needs the backend running (`make dev` in the repo root)
```

## Pages

| Route | What it shows |
|---|---|
| `/` | App overview and navigation |
| `/queue` | The review queue — real flagged patients, highest risk first |
| `/queue/[patientId]` | Case detail: start a review, watch the trace stream live (SSE), record a decision |
| `/evidence/fairness` | The subgroup fairness audit table |
| `/evidence/label-choice` | The label-choice experiment's divergence chart |

`CORS_ORIGINS` is configured on the backend (`COHORT_FRONTEND_ORIGINS`,
default `http://localhost:3000`) — the browser blocks cross-origin
fetch/EventSource calls otherwise.

## Testing

```bash
npx playwright test              # unit-style smoke tests, no backend needed
```

`e2e/home.spec.ts` only exercises the homepage (fetches nothing). The
queue/evidence pages fetch real data and are verified manually against a
live `make dev` backend rather than mocked — see the repo README's curl
examples.
