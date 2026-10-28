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

### Rebuilding the review queue

`make train` ends by running `python -m data.populate_queue`, which
**clears** every queued case, review event and paused review checkpoint
and then re-enqueues the patients the deployed model flags. Stop the API
before running it, and rerun it whenever `make data` regenerates the
cohort. Otherwise the queue would point at patients that no longer exist,
and **Start Review** answers 404 ("not in the scored cohort").

```bash
uv run python -m data.populate_queue
```

## Deploying (compose.prod.yaml)

For a complete step-by-step walkthrough (server setup, copying the data,
HTTPS, operations, troubleshooting) follow the
[Deployment guide](deployment.md). This section is the reference behind it.

The production stack publishes no host ports; a reverse proxy on the
external `edge` Docker network is the only way in. The API image
deliberately excludes `data/` and `artifacts/`; they are bind-mounted.

1. **Prepare data on the host.** Run `make data && make train` there, or
   copy `data/` (the `.db` and `interim/deidentified/` files) and
   `artifacts/registry/` from a machine that did. Either way, the queue
   must be built from the same cohort the API loads (see above).
2. **Set production values in `.env`:**
   - `COHORT_ENVIRONMENT=production` (JSON logs instead of the dev console format).
   - `WEB_PUBLIC_API_URL=https://your.domain/api`: inlined into the
     frontend bundle at build time, so rebuild after changing it.
   - `WEB_DOCS_URL` (optional, build time): where the app's **Docs** links
     point (passed to the frontend as `NEXT_PUBLIC_DOCS_URL`). Defaults to `https://zarreh.ai/clinical_care_navigator/`.
   - `COHORT_FRONTEND_ORIGINS='["https://your.domain"]'`: the CORS
     allow-list. Only needed if the API is served from a different
     origin than the frontend (the proxy layout below keeps them on one
     origin); the default allows localhost only.
   - `COHORT_OPENAI_API_KEY` (and optionally LangSmith) for reviews.
3. **Put the whole site behind authentication at the proxy.** The API
   has no user accounts: anyone who reaches `POST /queue/{id}/start` or
   `/decision` can launch LLM runs (which cost money) and record decisions.
   HTTP basic auth on the proxy covers both the frontend and the browser's
   direct API calls (the browser resends the credentials automatically).
4. **Make the proxy overwrite `X-Forwarded-For`.** The API trusts that
   header from any peer (`--forwarded-allow-ips "*"`, safe only because no
   port is published) and rate-limits per client IP. If the proxy appends
   to a client-supplied header instead of replacing it, clients can
   choose their own IP and bypass the limit.

Caddy (sets `X-Forwarded-For` from the real peer by default; generate the
hash with `caddy hash-password`):

```caddy
your.domain {
    basic_auth {
        reviewer $2a$14$...bcrypt-hash...
    }
    handle_path /api/* {
        reverse_proxy cohort-api:8000
    }
    reverse_proxy cohort-web:3000
}
```

nginx (create the file with `htpasswd -c /etc/nginx/.htpasswd reviewer`):

```nginx
server {
    server_name your.domain;
    auth_basic           "Cohort Risk Lab";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location /api/ {
        proxy_pass http://cohort-api:8000/;
        proxy_set_header X-Forwarded-For   $remote_addr;   # overwrite, don't append
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;                               # SSE review stream
    }
    location / {
        proxy_pass http://cohort-web:3000;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

Then:

```bash
docker compose -f compose.prod.yaml up -d --build
```

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
