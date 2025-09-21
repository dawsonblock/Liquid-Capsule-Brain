#!/bin/bash

echo "🧹 Cleaning up Capsule Brain project..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove duplicate/legacy configuration files
echo "Removing duplicate configuration files..."
rm -rf prometheus/ 2>/dev/null || true
rm -rf grafana/ 2>/dev/null || true
rm -f docker-compose.yml 2>/dev/null || true
rm -f docker-compose.override.yml 2>/dev/null || true
rm -f docker-compose.reverse-proxy.yml 2>/dev/null || true
rm -f logging_config.json 2>/dev/null || true

# Remove unused files (with confirmation)
echo "Checking for unused files..."

# Check if liquid_core is used
if ! grep -r "liquid_core" capsule_brain/ >/dev/null 2>&1; then
    echo "⚠️  capsule_brain/llm_adapter/liquid_core.py appears unused"
    read -p "Remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f capsule_brain/llm_adapter/liquid_core.py
        echo "✅ Removed liquid_core.py"
    fi
fi

# Check if run_overseer is used
if ! grep -r "run_overseer" capsule_brain/ >/dev/null 2>&1; then
    echo "⚠️  run_overseer.py appears unused"
    read -p "Remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f run_overseer.py
        echo "✅ Removed run_overseer.py"
    fi
fi

# Check if teacher directory is used
if ! grep -r "teacher" capsule_brain/ >/dev/null 2>&1; then
    echo "⚠️  teacher/ directory appears unused"
    read -p "Remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf teacher/
        echo "✅ Removed teacher/ directory"
    fi
fi

# Remove any .DS_Store files (macOS)
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null || true

# Remove any temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "Summary of what was removed:"
echo "- Python cache files (__pycache__, *.pyc, *.pyo)"
echo "- Duplicate configuration files (legacy locations)"
echo "- .DS_Store files"
echo "- Temporary files"
echo ""
echo "Files that may be unused (removed with confirmation):"
echo "- capsule_brain/llm_adapter/liquid_core.py"
echo "- run_overseer.py"
echo "- teacher/ directory"
