SHELL := /bin/bash

.PHONY: dev run docker build up down test fmt lint dev-setup typecheck coverage up-dev down-dev

dev:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn capsule_brain.api.server:app --host 0.0.0.0 --port 8000 --reload

run:
	python launch_capsule_brain.py

build:
	docker build -t capsule-brain:latest .

up:
	docker compose up --build

down:
	docker compose down

test:
	pytest -q

fmt:
	black . && isort .

lint:
	ruff check .


        main
dev-setup:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt && pre-commit install

typecheck:
	mypy .

coverage:
	coverage run -m pytest && coverage report -m

up-dev:
	docker compose up --build

down-dev:
	docker compose down
