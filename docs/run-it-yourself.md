# Run it yourself

```bash
uv sync --extra dev
cp .env.example .env   # fill in your own OpenAI API key
make test
make dev               # http://localhost:8000/healthz
```

Full quickstart (data generation, training, frontend) is written as each
phase lands.
