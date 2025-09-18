#!/bin/bash
# Setup script for Liquid Capsule Brain development environment

set -e

echo "🧠 Setting up Liquid Capsule Brain development environment..."

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "🔧 Installing pre-commit hooks..."
    pre-commit install
else
    echo "⚠️  pre-commit not available, skipping hooks installation"
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Run validation
echo "🔍 Running build validation..."
python3 validate_build.py

echo ""
echo "🎉 Setup complete! Next steps:"
echo "   1. Edit .env file with your API keys and configuration"
echo "   2. Run 'make dev' to start development server"
echo "   3. Run 'make help' to see all available commands"
echo ""
echo "📚 Documentation: docs/README.md"
echo "🏗️  Project structure: PROJECT_STRUCTURE.md"
