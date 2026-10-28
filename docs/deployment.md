# Deployment guide

A step-by-step guide to putting the app on a Linux server behind HTTPS
with a password. Follow the steps in order; each ends with a check.

```
browser ──HTTPS + password──▶ Caddy (ports 80/443) ──▶ cohort-web :3000  (Next.js)
                                    │
                                    └── /api/* ───────▶ cohort-api :8000 (FastAPI)
                                                          reads data/ and artifacts/
```

Only Caddy is reachable from the internet. The app containers publish no
ports and talk to Caddy over a Docker network called `edge`.

## What you need

- **A Linux server** (Ubuntu 22.04/24.04 assumed) with **8 GB RAM**
  (building the feature table peaks at about 4.5 GB), 2+ vCPU and
  **10 GB free disk**.
- **A domain name** with a DNS `A` record pointing at the server, e.g.
  `cohort.example.com`.
- **An OpenAI API key**: reviews call the LLM. Everything else works without it.
- **Your local copy of the project** with data already generated
  (`make data && make train` done). The server does not need Python,
  Java or Synthea.

In the commands below, replace `cohort.example.com` with your domain and
`user@server` with your SSH login.

## 1. Prepare the server

```bash
ssh user@server
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # then log out and back in
sudo apt-get install -y git rsync
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

**Check:** `docker run --rm hello-world` prints "Hello from Docker!".

## 2. Get the code

```bash
git clone https://github.com/zarreh/cohort_risk_lab.git
cd cohort_risk_lab
```

## 3. Copy the data from your machine

The app needs about 550 MB of generated data, not the 6.7 GB raw Synthea
output. Run this **on your local machine**, from the project folder:

```bash
rsync -avz --progress data/cohort.db              user@server:cohort_risk_lab/data/
rsync -avz --progress data/interim/deidentified/  user@server:cohort_risk_lab/data/interim/deidentified/
rsync -avz --progress artifacts/registry/         user@server:cohort_risk_lab/artifacts/registry/
```

!!! note "Alternative: generate the data on the server"
    Install `uv` and a JDK 17+, then run `make data && make train` as in
    [Run it yourself](run-it-yourself.md). It takes 10-15 minutes and
    needs about 8 GB more disk.

**Check (on the server):** `ls artifacts/registry` shows `v1_burden` and
`v1_cost`.

## 4. Create the `.env` file

On the server, in `cohort_risk_lab/`:

```bash
cat > .env <<'EOF'
COHORT_ENVIRONMENT=production
COHORT_OPENAI_API_KEY=sk-...your key...
WEB_PUBLIC_API_URL=https://cohort.example.com/api
# Optional
# COHORT_LANGSMITH_API_KEY=...
# WEB_DOCS_URL=https://zarreh.ai/clinical_care_navigator/
EOF
chmod 600 .env
```

| Variable | What it does |
|---|---|
| `COHORT_ENVIRONMENT` | `production` switches logs to JSON |
| `COHORT_OPENAI_API_KEY` | Needed to run case reviews |
| `WEB_PUBLIC_API_URL` | Where the browser calls the API. Built into the frontend, so **rebuild** after changing it |
| `COHORT_LANGSMITH_API_KEY` | Optional tracing |
| `WEB_DOCS_URL` | Optional; where the app's **Docs** links point |

## 5. Build the images and the review queue

```bash
docker network create edge
docker compose -f compose.prod.yaml build
docker compose -f compose.prod.yaml run --rm cohort-api python -m data.populate_queue
```

**Check:** the last command prints something like
`Enqueued 15,989 of 33,805 patients (threshold 0.18)`.

## 6. Start the app

```bash
docker compose -f compose.prod.yaml up -d
docker compose -f compose.prod.yaml ps
```

**Check:** both `cohort-api` and `cohort-web` show `(healthy)` within a
minute.

## 7. Put Caddy in front (HTTPS + password)

Caddy gets a free TLS certificate automatically and asks for a password.

Create a password hash (pick your own password):

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'choose-a-strong-password'
```

Create a folder for the proxy, **next to** (not inside) the project:

```bash
mkdir -p ~/proxy && cd ~/proxy
```

`~/proxy/Caddyfile`, pasting the hash from above:

```caddy
cohort.example.com {
	basic_auth {
		reviewer $2a$14$...paste-the-hash-here...
	}
	handle_path /api/* {
		reverse_proxy cohort-api:8000
	}
	reverse_proxy cohort-web:3000
}
```

`~/proxy/compose.yaml`:

```yaml
services:
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - edge

volumes:
  caddy_data:
  caddy_config:

networks:
  edge:
    external: true
```

```bash
docker compose up -d
docker compose logs -f caddy     # wait for "certificate obtained successfully", then Ctrl-C
```

!!! tip "Already running a reverse proxy for other apps?"
    Skip the proxy compose file: add the site block above to your existing
    Caddy config (or the nginx example in
    [Run it yourself](run-it-yourself.md#deploying-composeprodyaml)) and
    make sure that proxy is on the `edge` network. Whatever proxy you use
    must **replace** `X-Forwarded-For`, not append to it. Caddy does this
    by default.

## 8. Verify

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://cohort.example.com/                 # 401
curl -s -u reviewer:YOUR_PASSWORD https://cohort.example.com/api/healthz             # {"status":"ok"}
```

Then in a browser:

1. Open `https://cohort.example.com` and sign in as `reviewer`.
2. Open **Review queue**, then any patient, then **Start AI review**. The
   steps stream in and a brief appears in about 20-60 s.
3. Choose **Defer** and check that the decision is recorded.

The first review and the label-choice page are slow once (about 10 s)
after each restart while the API loads the cohort.

## Day-to-day operations

**Update to the latest code**

```bash
cd ~/cohort_risk_lab
git pull
docker compose -f compose.prod.yaml up -d --build
```

**After regenerating the data** (new `make data && make train` locally)

```bash
# locally: rerun the three rsync commands from step 3, then on the server:
docker compose -f compose.prod.yaml stop cohort-api
docker compose -f compose.prod.yaml run --rm cohort-api python -m data.populate_queue
docker compose -f compose.prod.yaml up -d
```

`populate_queue` **deletes every review and decision** and rebuilds the
queue from the current data. That is required after new data, and also
a quick way to reset a demo.

**Logs:** `docker compose -f compose.prod.yaml logs -f cohort-api`

**Back up reviews and decisions:** copy `data/queue.db` and
`data/checkpoints.db` (ideally while the API is stopped).

**Change the password:** generate a new hash (step 7), edit the
Caddyfile, then `cd ~/proxy && docker compose restart caddy`.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Browser keeps asking for the password | Wrong password, or the hash was pasted incompletely. Regenerate it (step 7) |
| Pages say "Could not reach the backend" | The API isn't healthy (`docker compose -f compose.prod.yaml ps`, then check its logs), or `WEB_PUBLIC_API_URL` is wrong. Fix `.env` and run `up -d --build` |
| **Start AI review** fails with 500 | `COHORT_OPENAI_API_KEY` missing or invalid. Fix `.env`, then `up -d` |
| **Start AI review** says "not in the scored cohort" | Queue built from older data. Rerun `populate_queue` (see above) |
| Caddy can't get a certificate | DNS doesn't point at the server yet, or ports 80/443 are blocked |
| `network edge declared as external, but could not be found` | Run `docker network create edge` |
| `cohort-api` restarts or gets killed | Not enough memory. Use a server with 8 GB RAM |
