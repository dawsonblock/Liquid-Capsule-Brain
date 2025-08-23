# Contributing

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

## Quality gates
- `ruff check .`  — lint
- `black .` & `isort .` — format
- `mypy .` — type check
- `pytest -q` — tests
