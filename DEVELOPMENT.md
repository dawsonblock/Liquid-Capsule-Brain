# Development Guide

This guide covers development workflows, best practices, and common tasks for the Liquid Capsule Brain project.

## Quick Start for Developers

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd Liquid-Capsule-Brain
   ./scripts/setup.sh
   ```

2. **Start Development**:
   ```bash
   make dev  # Starts development server with auto-reload
   ```

3. **Health Check**:
   ```bash
   ./scripts/health-check.sh  # Verify everything is working
   ```

## Development Workflow

### Daily Development
```bash
# Start your day
make dev                    # Start development server
./scripts/health-check.sh   # Verify services

# During development
make test                   # Run tests
make lint                   # Check code style
make fmt                    # Format code

# End of day
make clean                  # Clean up cache files
```

### Code Quality
```bash
make lint       # Ruff linting
make typecheck  # MyPy type checking
make fmt        # Black + isort formatting
make test       # Pytest test suite
make coverage   # Test coverage report
```

## Project Structure

The project follows a modular architecture:

- `capsule_brain/` - Core application code
- `config/` - All configuration files
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `tests/` - Test suites

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information.

## Configuration Management

### Environment Variables
- Copy `.env.example` to `.env`
- Set your API keys and configuration
- Never commit `.env` files

### Docker Configuration
- Production: `config/docker/docker-compose.yml`
- Development: `config/docker/docker-compose.override.yml`
- Reverse Proxy: `config/docker/docker-compose.reverse-proxy.yml`

### Monitoring
- Prometheus: `config/monitoring/prometheus/`
- Grafana: `config/monitoring/grafana/`

## API Development

### Adding New Endpoints
1. Add route to `capsule_brain/api/server.py`
2. Add tests to `tests/test_api.py`
3. Update documentation

### LLM Integration
- Add new LLM clients to `capsule_brain/llm_adapter/`
- Follow the pattern in `deepseek_client.py`
- Update `belief_state_manager.py` to use new client

## Testing

### Running Tests
```bash
make test           # Run all tests
pytest tests/       # Run specific test directory
pytest -v           # Verbose output
pytest -k "test_name"  # Run specific test
```

### Writing Tests
- Place tests in `tests/` directory
- Follow naming convention: `test_*.py`
- Use pytest fixtures for setup
- Mock external dependencies

## Docker Development

### Local Development
```bash
make up-dev     # Start development stack
make down-dev   # Stop development stack
```

### Production Testing
```bash
make up         # Start production stack
make down       # Stop production stack
```

### Building Images
```bash
make build      # Build production image
docker build -f Dockerfile.dev -t capsule-brain:dev .  # Build dev image
```

## Debugging

### API Debugging
- Check logs in terminal where `make dev` is running
- Use `/healthz` and `/ready` endpoints
- Check `/metrics` for performance data

### Docker Debugging
```bash
docker logs <container-name>    # View container logs
docker exec -it <container> sh  # Shell into container
```

### Common Issues
1. **Port conflicts**: Change ports in docker-compose files
2. **Permission errors**: Check file permissions on scripts
3. **API key errors**: Verify `.env` configuration

## Contributing

### Before Submitting PR
1. Run full test suite: `make test`
2. Check code quality: `make lint typecheck`
3. Format code: `make fmt`
4. Update documentation if needed
5. Add tests for new features

### Commit Messages
Follow conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/changes

## Deployment

### Local Deployment
```bash
make up  # Production stack locally
```

### Production Deployment
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Monitoring and Observability

### Metrics
- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3000`
- API metrics: `http://localhost:8000/metrics`

### Health Checks
- API health: `http://localhost:8000/healthz`
- API ready: `http://localhost:8000/ready`
- Service status: `./scripts/health-check.sh`

## Troubleshooting

### Common Commands
```bash
make help                   # Show all available commands
./scripts/health-check.sh   # Check service health
make clean                  # Clean cache files
docker system prune         # Clean Docker resources
```

### Getting Help
1. Check this guide and [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. Review documentation in `docs/`
3. Check existing issues and tests
4. Ask questions in team channels

## Performance Tips

1. **Development**: Use `make dev` for auto-reload
2. **Testing**: Use `pytest -x` to stop on first failure
3. **Docker**: Use `make up-dev` for development stack
4. **Debugging**: Enable verbose logging in `.env`

This guide should cover most development scenarios. For specific deployment or advanced configuration, see the documentation in the `docs/` directory.
