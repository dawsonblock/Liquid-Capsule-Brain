# Configuration Directory

This directory contains all configuration files for the Liquid Capsule Brain system.

## Files

- `logging_config.json` - Logging configuration
- `docker/` - Docker-related configuration files
- `monitoring/` - Prometheus and Grafana configurations
- `deployment/` - Deployment-specific configurations

## Environment Variables

Environment variables are managed through `.env` files in the project root:
- `.env` - Local development configuration (not committed)
- `.env.example` - Template for environment variables
- `.env.reverse-proxy.example` - Template for reverse proxy setup
