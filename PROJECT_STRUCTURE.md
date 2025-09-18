# Project Structure

This document describes the organization of the Liquid Capsule Brain repository.

## Root Directory

```
liquid-capsule-brain/
├── README.md                    # Main project documentation
├── BUILD_CONFIG.md             # Build and setup instructions
├── PROJECT_STRUCTURE.md        # This file
├── CONTRIBUTING.md             # Contribution guidelines
├── CODE_OF_CONDUCT.md          # Code of conduct
├── LICENSE                     # Project license
├── RELEASE_NOTES.md            # Release notes
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variables template
├── .env.reverse-proxy.example  # Reverse proxy env template
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── Makefile                    # Build automation
├── Dockerfile                  # Production Docker image
├── Dockerfile.dev              # Development Docker image
├── launch_capsule_brain.py     # Main application launcher
├── run_overseer.py             # Overseer service launcher
└── validate_build.py           # Build validation script
```

## Core Application (`capsule_brain/`)

The main application code organized by functionality:

```
capsule_brain/
├── __init__.py                 # Package initialization
├── api/                        # FastAPI web interface
│   ├── server.py              # Main FastAPI application
│   ├── dependencies.py        # Dependency injection
│   └── routes/                # API route definitions
├── core/                       # Core AGI components
│   ├── capsule_engine.py      # Main engine orchestrator
│   ├── belief_state_manager.py # Working memory management
│   ├── alignment_core.py      # Ethical alignment system
│   ├── iit_analyzer.py        # Integrated Information Theory
│   └── self_wiring.py         # Self-modification system
├── llm_adapter/               # LLM integrations
│   ├── liquid_core.py         # Mock liquid neural network
│   └── deepseek_client.py     # DeepSeek V3 integration
├── gui/                       # Web interface components
├── security/                  # Authentication & authorization
├── observability/             # Monitoring & telemetry
├── planner/                   # Task planning system
├── retrieval/                 # Knowledge retrieval
└── tools/                     # External tool integrations
```

## Configuration (`config/`)

All configuration files organized by purpose:

```
config/
├── README.md                   # Configuration documentation
├── logging_config.json         # Logging configuration
├── docker/                     # Docker configurations
│   ├── docker-compose.yml     # Production compose file
│   ├── docker-compose.override.yml # Development overrides
│   └── docker-compose.reverse-proxy.yml # Reverse proxy setup
└── monitoring/                 # Monitoring configurations
    ├── prometheus/             # Prometheus configuration
    │   ├── prometheus.yml     # Main Prometheus config
    │   └── alerts.yml         # Alert rules
    └── grafana/               # Grafana dashboards & config
```

## Documentation (`docs/`)

Comprehensive documentation organized by topic:

```
docs/
├── README.md                   # Documentation index
├── README_EXTENDED.md          # Detailed system overview
├── DEPLOYMENT.md              # Deployment instructions
├── MONITORING.md              # Monitoring setup
├── ALERTING.md                # Alert configuration
├── SECURITY.md                # Security guidelines
├── DEV_DOCKER.md              # Docker development
├── DEV_COMPOSE.md             # Compose development
├── HELM.md                    # Kubernetes Helm charts
├── HELMFILE.md                # Helmfile deployment
├── GITOPS_TERRAFORM.md        # Infrastructure as Code
├── TLS_REVERSE_PROXY.md       # SSL/TLS setup
└── SEALED_SECRETS.md          # Secret management
```

## Deployment & Infrastructure

```
deploy/                         # Deployment configurations
k8s/                           # Kubernetes manifests
teacher/                       # AI Overseer service
scripts/                       # Utility scripts
```

## Testing & Quality

```
tests/                         # Test suites
├── test_api.py               # API endpoint tests
├── test_gui.py               # GUI component tests
├── test_di_overrides.py      # Dependency injection tests
└── ...
```

## Monitoring & Observability

```
grafana/                      # Grafana configurations (legacy)
prometheus/                   # Prometheus configurations (legacy)
```

> **Note**: Monitoring configurations are being moved to `config/monitoring/`

## Development Files

```
.venv/                        # Python virtual environment
.mypy_cache/                  # MyPy type checker cache
.pytest_cache/                # Pytest cache
.ruff_cache/                  # Ruff linter cache
__pycache__/                  # Python bytecode cache
```

## Key Design Principles

1. **Separation of Concerns**: Each directory has a clear, single responsibility
2. **Configuration Centralization**: All config files in `config/` directory
3. **Documentation Organization**: Structured docs with clear navigation
4. **Development Workflow**: Clear separation between dev and prod configurations
5. **Monitoring Integration**: Built-in observability and alerting
6. **Security First**: Dedicated security module and configurations
7. **Extensibility**: Modular design for easy feature additions

## File Naming Conventions

- **Python files**: `snake_case.py`
- **Configuration files**: `kebab-case.yml` or `snake_case.json`
- **Documentation**: `UPPERCASE.md` for main docs, `lowercase.md` for specific topics
- **Docker files**: `Dockerfile` and `Dockerfile.dev`
- **Environment files**: `.env.example`, `.env.reverse-proxy.example`

## Import Path Structure

```python
# Core components
from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.api.server import app

# LLM integrations
from capsule_brain.llm_adapter.deepseek_client import DeepSeekClient

# Security
from capsule_brain.security.admin import require_admin_token
```

This structure promotes maintainability, scalability, and clear separation of concerns while making the codebase easy to navigate for new contributors.
