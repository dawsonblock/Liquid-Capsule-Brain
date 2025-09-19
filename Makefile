SHELL := /bin/bash

.PHONY: dev run docker build up down test fmt lint dev-setup typecheck coverage up-dev down-dev clean

# Development commands
dev:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python launch_capsule_brain.py

run:
	python launch_capsule_brain.py

# Docker commands (using root directory configs for now)
build:
	docker build -t capsule-brain:latest .

up:
	docker compose -f config/docker/docker-compose.yml -f config/docker/docker-compose.override.yml up --build -d

up-dev:
	docker compose -f config/docker/docker-compose.yml -f config/docker/docker-compose.override.yml up --build

down:
	docker compose -f config/docker/docker-compose.yml -f config/docker/docker-compose.override.yml down

down-dev:
	docker compose -f config/docker/docker-compose.yml -f config/docker/docker-compose.override.yml down

test:
	pytest -q

fmt:
	black . && isort .

lint:
	ruff check .

dev-setup:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt && pre-commit install

typecheck:
	mypy .

coverage:
	coverage run -m pytest && coverage report -m

# Cleanup commands
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name ".ruff_cache" -delete

# Help command
help:
	@echo "Available commands:"
	@echo "  dev        - Start development server with auto-reload"
	@echo "  run        - Run production server"
	@echo "  build      - Build Docker image"
	@echo "  up         - Start production services with Docker Compose"
	@echo "  up-dev     - Start development services with Docker Compose"
	@echo "  down       - Stop production services"
	@echo "  down-dev   - Stop development services"
	@echo "  test       - Run tests"
	@echo "  fmt        - Format code with black and isort"
	@echo "  lint       - Lint code with ruff"
	@echo "  typecheck  - Type check with mypy"
	@echo "  coverage   - Run tests with coverage report"
	@echo "  dev-setup  - Setup development environment"
	@echo "  clean      - Clean up cache files"
	@echo "  help       - Show this help message"
