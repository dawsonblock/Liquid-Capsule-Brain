# Scripts Directory

This directory contains utility scripts for the Liquid Capsule Brain project.

## Available Scripts

### `setup.sh`
**Purpose**: Automated development environment setup

**Usage**:
```bash
./scripts/setup.sh
```

**What it does**:
- Checks Python version compatibility (3.11+)
- Creates virtual environment if it doesn't exist
- Installs all dependencies (production + development)
- Sets up pre-commit hooks
- Creates `.env` file from template
- Runs build validation
- Provides next steps guidance

### `health-check.sh`
**Purpose**: Comprehensive health check for all services

**Usage**:
```bash
./scripts/health-check.sh
```

**Environment Variables**:
- `API_URL` - API base URL (default: http://localhost:8000)
- `ADMIN_TOKEN` - Admin token for protected endpoints (default: dev-secure-token-123)
- `PROMETHEUS_URL` - Prometheus URL (default: http://localhost:9090)
- `GRAFANA_URL` - Grafana URL (default: http://localhost:3000)

**What it checks**:
- API health and ready endpoints
- API metrics endpoint
- API query functionality
- Prometheus availability and query API
- Grafana health
- Docker container status

## Making Scripts Executable

Before running any script, make sure it's executable:

```bash
chmod +x scripts/*.sh
```

## Integration with Makefile

These scripts can be integrated with the Makefile for easier access:

```bash
# Add to Makefile
setup:
	./scripts/setup.sh

health:
	./scripts/health-check.sh
```

## Best Practices

1. **Error Handling**: All scripts use `set -e` for fail-fast behavior
2. **Environment Variables**: Scripts respect environment variables for configuration
3. **User Feedback**: Clear output with emojis and status indicators
4. **Cross-platform**: Scripts are designed to work on macOS and Linux
5. **Documentation**: Each script includes inline comments explaining its purpose

## Adding New Scripts

When adding new scripts:

1. Place them in this directory
2. Make them executable: `chmod +x script-name.sh`
3. Add documentation to this README
4. Follow the existing naming convention (kebab-case)
5. Include proper error handling and user feedback
6. Test on multiple platforms if possible
