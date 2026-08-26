# Run it yourself

## Quick path — backend only, using the committed sample

```bash
uv sync --extra dev
cp .env.example .env   # OpenAI key optional — only the evidence agent's LLM nodes need it
make test              # 120 tests, no external data required
make validate          # ML metric floors + canonical brief scenarios, against committed fixtures
make dev               # http://localhost:8000/healthz
```

This gets you a green test suite and a running API server without
generating any data. The API's data-backed routes (`/queue`,
`/evidence/*`) need the full pipeline below.

## Full path — generate the cohort, train, and run the frontend

Requires a JDK 17+ (Synthea needs one; `data/generate_synthea.py` prints
an install command if none is found — no root required) and roughly
10-15 minutes, most of it Synthea generating ~30,000 patients.

```bash
make data    # generate_synthea -> deidentify -> build_cohort -> inject_access_gap -> build_cohort_store
make train   # trains v1_burden and v1_cost, populates the review queue
make dev             # http://localhost:8000/healthz
make frontend-dev    # http://localhost:3000, in a second terminal
```

Then, with an OpenAI key in `.env`:

1. Open `http://localhost:3000/queue` — the real review queue, highest
   risk first.
2. Open any patient — **Start Review** streams the evidence agent's
   trace live over SSE, ending at a drafted case brief and a decision
   form (enroll / decline / defer).
3. Open `/evidence/fairness` — the per-stratum audit for the deployed
   model.
4. Open `/evidence/label-choice` — the label-choice divergence chart.

Without an OpenAI key, everything up to **Start Review** still works —
the queue, case detail, and both evidence pages all render real data from
the trained models. Starting a review will fail at the point it needs to
call the LLM; this is expected and disclosed on the case page.

## Regenerating docs assets

```bash
make docs-assets       # regenerates docs/evidence/assets/*.svg from the trained models
make docs-screenshots  # re-captures docs/assets/homepage-screenshot.png via Playwright
make docs              # serves the MkDocs site locally
```

## Regenerating the validation harness's frozen fixture

Only needed if you want to re-seed it (e.g. after a new `make data` run
with a different Synthea seed) — this is not part of `make data` or CI:

```bash
PYTHONPATH=. uv run python -m validation.fixtures.build_frozen_fixture
```
