#!/bin/bash
# Development environment setup script
# Usage: ./scripts/setup-dev.sh

set -e

echo "🚀 Setting up QU Security Backend development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install pre-commit
echo "🪝 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Install additional development tools
echo "🛠️  Installing development tools..."
pip install coverage pytest-django

# Run initial code formatting
echo "📝 Running initial code formatting..."
ruff format .
ruff check . --fix

# Create local environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating local .env file from template..."
    cp .env.local .env
    echo "✅ Created .env file for local development"
    echo "📝 You can customize .env with your local database settings"
else
    echo "📄 .env file already exists, skipping creation"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set up your local PostgreSQL database"
echo "2. Run: python manage.py migrate"
echo "3. Run: python manage.py createsuperuser"
echo "4. Run: python manage.py runserver"
echo ""
echo "🛠️  Development commands:"
echo "• Format code: ./scripts/format.sh"
echo "• Run tests: python manage.py test"
echo "• Deploy: zappa update dev"
