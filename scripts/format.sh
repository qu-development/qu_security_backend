#!/bin/bash
# Format and lint code with Ruff
# Usage: ./scripts/format.sh

set -e

echo "🚀 Running Ruff formatter and linter..."

# Format code
echo "📝 Formatting code with Ruff..."
ruff format .

# Fix linting issues
echo "🔧 Fixing linting issues..."
ruff check . --fix

# Show remaining issues (if any)
echo "📊 Checking for remaining issues..."
ruff check .

echo "✅ Code formatting and linting complete!"
