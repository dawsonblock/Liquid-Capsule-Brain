# Build Configuration Files

This document describes the configuration files needed to build and run Liquid Capsule Brain.

## Environment Configuration

### `.env.example`
Main environment configuration template. Copy to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables:
- `HOST`, `PORT` - API server binding
- `ADMIN_TOKEN`, `ADMIN_API_KEY` - Authentication
- `OPENAI_API_KEY` - LLM provider API key
- `TELEMETRY_ENABLE` - Monitoring toggle

### `.env.reverse-proxy.example`
Template for TLS reverse proxy setup. Copy to `.env` when using:

```bash
cp .env.reverse-proxy.example .env
# Configure CB_DOMAIN and certificates
docker compose -f docker-compose.yml -f docker-compose.reverse-proxy.yml --env-file .env up --build
```

## Build Process

### Prerequisites Check
Run the validation script to verify all prerequisites:

```bash
python3 validate_build.py
```

### Local Development
```bash
# Setup development environment
make dev-setup

# Start development server
make dev
```

### Docker Build
```bash
# Build Docker image
make build

# Run with Docker Compose
make up
```

### Available Make Targets
- `dev-setup` - Install dependencies and setup pre-commit hooks
- `dev` - Start development server with auto-reload
- `run` - Run production server
- `build` - Build Docker image
- `up`/`down` - Docker Compose operations
- `test` - Run tests
- `lint` - Code linting with ruff
- `fmt` - Code formatting with black and isort
- `typecheck` - Type checking with mypy
- `coverage` - Test coverage report

## Compatibility Notes

- **Python**: 3.11+ recommended, 3.12+ supported
- **PyTorch**: Updated to 2.2.0 for Python 3.12 compatibility
- **Docker**: SSL trust flags added for corporate networks

## Files Added/Modified

### Added:
- `.env.example` - Main environment template
- `.env.reverse-proxy.example` - TLS proxy template
- `validate_build.py` - Build validation script
- `BUILD_CONFIG.md` - This documentation

### Modified:
- `requirements.txt` - PyTorch version updated
- `Makefile` - Cleaned up duplicate targets
- `.gitignore` - Added .env and .venv/
- `Dockerfile` - Added SSL trust flags