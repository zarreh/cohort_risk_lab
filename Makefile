.PHONY: dev test lint typecheck imports validate up down data train docs docs-assets docs-screenshots frontend-dev frontend-build frontend-types frontend-e2e

dev:
	uv run uvicorn cohort.api.main:app --reload --port 8000

test:
	uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

imports:
	PYTHONPATH=src uv run lint-imports

validate:
	uv run python -m validation.run

up:
	docker compose up --build

down:
	docker compose down

data:
	uv run python -m data.generate_synthea
	uv run python -m data.deidentify
	uv run python -m data.build_cohort
	uv run python -m data.inject_access_gap
	uv run python -m data.build_cohort_store

train:
	uv run python -m cohort.pipeline.models.train --label Y_BURDEN --version v1_burden
	uv run python -m cohort.pipeline.models.train --label Y_COST --version v1_cost
	uv run python -m data.populate_queue

docs:
	uv run mkdocs serve

docs-assets:
	PYTHONPATH=. uv run python docs/generate_plots.py

docs-screenshots:
	cd frontend && npx playwright test capture-screenshots.spec.ts

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-types:
	PYTHONPATH=src uv run python -c "from cohort.api.main import app; import json; json.dump(app.openapi(), open('frontend/openapi.json', 'w'), indent=2)"
	cd frontend && npm run gen:types

frontend-e2e:
	cd frontend && npx playwright test review.spec.ts
