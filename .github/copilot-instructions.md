# Liquid Capsule Brain Supreme AGI Development Instructions

**ALWAYS follow these instructions first and fallback to additional search and context gathering only if the information here is incomplete or found to be in error.**

## Project Overview
Liquid Capsule Brain is a Python 3.11+ FastAPI application implementing an AI system with dynamic belief networks, self-wiring cognition, AI overseer for ethical alignment, and real-time WebSocket GUI. The system includes integrated monitoring with Prometheus/Grafana.

## Working Effectively

### Prerequisites and Environment Setup
```bash
# ALWAYS start with validation
python3 validate_build.py

# Copy and configure environment 
cp .env.example .env
# Edit .env with your API keys and settings

# Bootstrap development environment - NEVER CANCEL: Takes 2 minutes
make dev-setup
```
**NEVER CANCEL** the `make dev-setup` command. It takes approximately 2 minutes to install all Python dependencies and configure pre-commit hooks. Set timeout to 5+ minutes.

### Development Workflow
```bash
# ALWAYS activate virtual environment first
source .venv/bin/activate

# Start development server - starts immediately
export PYTHONPATH=$(pwd)
python launch_capsule_brain.py
# API available at: http://127.0.0.1:8000
# Health check: curl http://127.0.0.1:8000/healthz

# Alternative development server with auto-reload
make dev
```

### Code Quality and Testing
```bash
# ALWAYS activate virtual environment first
source .venv/bin/activate

# Format code - takes <1 second
make fmt

# Lint code - takes <1 second, expect ~189 style warnings
make lint

# Run tests - CRITICAL: Must set PYTHONPATH
export PYTHONPATH=$(pwd)
make test
# Tests complete in <1 second: 5 passed, 1 skipped

# Type checking - WARNING: Has module path conflicts
make typecheck  # Currently fails due to module path issues

# Coverage report
make coverage
```

**CRITICAL**: Always run `export PYTHONPATH=$(pwd)` before running tests or the imports will fail.

### Docker Operations
```bash
# Build Docker image - NEVER CANCEL: Takes 2.5 minutes
make build
# Set timeout to 5+ minutes. Build includes PyTorch and all dependencies.

# Docker Compose - WARNING: SSL certificate issues in development
make up
# KNOWN ISSUE: Fails with SSL certificate verification errors in sandboxed environments
# Use local development server instead: python launch_capsule_brain.py
```

**NEVER CANCEL** Docker builds. The `make build` command takes approximately 2.5 minutes due to PyTorch installation. Set timeout to 5+ minutes minimum.

## Validation Scenarios

### Complete Development Scenario
After making any changes, ALWAYS validate with this complete scenario:
```bash
# 1. Validate environment
python3 validate_build.py

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Format and lint
make fmt
make lint  # Expect style warnings - check for new errors only

# 4. Test with proper PYTHONPATH
export PYTHONPATH=$(pwd)
make test

# 5. Start server and test functionality
python launch_capsule_brain.py &
sleep 3
curl http://127.0.0.1:8000/healthz  # Should return {"ok":true}
curl http://127.0.0.1:8000/ready    # Should return {"ready":true}
curl http://127.0.0.1:8000/state/summary  # Should return system state JSON
pkill -f "python launch_capsule_brain.py"
```

### Manual UI Testing
```bash
# Start the API server
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python launch_capsule_brain.py

# Test core endpoints:
# - GET /healthz - Health check
# - GET /ready - Readiness check  
# - GET /state/summary - System state with belief metrics
# - POST /ask - Chat interface
# - WebSocket /ws - Real-time updates
```

## Build Timing and Timeouts

| Command | Expected Time | Recommended Timeout | Notes |
|---------|---------------|-------------------|-------|
| `python3 validate_build.py` | <1 second | 1 minute | Prerequisites check |
| `make dev-setup` | ~2 minutes | 5 minutes | **NEVER CANCEL** - Installs PyTorch |
| `make fmt` | <1 second | 1 minute | Code formatting |
| `make lint` | <1 second | 1 minute | Linting with ruff |
| `make test` | <1 second | 2 minutes | With PYTHONPATH set |
| `make typecheck` | <1 second | 1 minute | Currently has issues |
| `make build` | ~2.5 minutes | 5 minutes | **NEVER CANCEL** - Docker build |
| `make up` | Variable | 5 minutes | Docker Compose (has SSL issues) |

## Known Issues and Workarounds

### Docker Compose SSL Issues
Docker Compose fails in sandboxed environments due to SSL certificate verification:
```
ERROR: Could not find a version that satisfies the requirement fastapi==0.110.0
```
**Workaround**: Use local development server instead of Docker Compose.

### Type Checking Module Conflicts  
`make typecheck` fails with:
```
Source file found twice under different module names
```
**Workaround**: Type checking currently not functional. Focus on linting and testing.

### Test Import Issues
Tests fail without PYTHONPATH:
```
ModuleNotFoundError: No module named 'capsule_brain'
```
**Solution**: Always run `export PYTHONPATH=$(pwd)` before testing.

## Repository Structure

### Key Directories
```
capsule_brain/          # Main application code
├── api/               # FastAPI server and endpoints
├── core/              # Belief state, self-wiring, alignment
├── gui/               # WebSocket GUI and static files
├── llm_adapter/       # LLM integration layer
├── observability/     # Prometheus metrics
├── planner/           # Task planning system
├── retrieval/         # Document indexing and search
├── security/          # Input sanitization and secrets
└── tools/             # Utility aggregator

tests/                 # Test suite
scripts/               # Development and deployment scripts
docs/                  # Extended documentation
deploy/                # Kubernetes and infrastructure
```

### Important Files
- `launch_capsule_brain.py` - Main application entry point
- `validate_build.py` - Environment validation script
- `.env.example` - Environment configuration template
- `Makefile` - Build and development commands
- `requirements.txt` - Core Python dependencies
- `requirements-dev.txt` - Development tools

## CI/CD Integration
The GitHub Actions workflow (`.github/workflows/python-app.yml`) runs:
1. Python 3.10 setup (note: differs from local 3.11+ requirement)
2. pip install with flake8 and pytest
3. PYTHONPATH configuration
4. flake8 linting
5. pytest execution

**Critical**: Local development uses ruff/black instead of flake8. Always run `make fmt && make lint` before committing.

## Security Notes
- Never commit secrets to `.env` files
- Require `ADMIN_TOKEN` for overseer endpoints
- Rate-limit public endpoints in production
- Validate tool invocations rigorously

## Common Tasks

### Adding New Features
1. Activate virtual environment: `source .venv/bin/activate`
2. Make code changes
3. Run `make fmt` to format
4. Run `make lint` and fix any NEW errors
5. Set `export PYTHONPATH=$(pwd)` and run `make test`
6. Manually test API endpoints
7. Commit changes

### Debugging Issues
1. Check `python3 validate_build.py` for environment issues
2. Verify `.env` configuration matches `.env.example`
3. Ensure PYTHONPATH is set for any Python module imports
4. Check server logs for detailed error messages
5. Use `curl` to test API endpoints directly

### Performance Monitoring
- Prometheus metrics: `GET /metrics`
- Health endpoints: `GET /healthz`, `GET /ready`
- State summary: `GET /state/summary`
- Grafana dashboard: http://127.0.0.1:3000 (if Docker Compose working)

Always ensure your changes maintain the system's real-time responsiveness and monitoring capabilities.