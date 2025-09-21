#!/bin/bash

echo "🧹 Safe cleanup of Capsule Brain project..."

# Remove Python cache files (always safe)
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove duplicate configuration files (safe - using config/ versions)
echo "Removing duplicate configuration files..."
rm -rf prometheus/ 2>/dev/null || true
rm -rf grafana/ 2>/dev/null || true
rm -f docker-compose.yml 2>/dev/null || true
rm -f docker-compose.override.yml 2>/dev/null || true
rm -f docker-compose.reverse-proxy.yml 2>/dev/null || true
rm -f logging_config.json 2>/dev/null || true

# Remove system files
echo "Removing system files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true

echo "✅ Safe cleanup complete!"
echo ""
echo "Removed:"
echo "- Python cache files"
echo "- Duplicate configuration files (legacy locations)"
echo "- System files (.DS_Store, Thumbs.db)"
echo "- Temporary files"
