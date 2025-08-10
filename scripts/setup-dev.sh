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
    echo "📄 Creating local .env file..."
    cat > .env << 'EOF'
# Local Development Environment
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Local Database
DB_NAME=qu_security_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# S3 Configuration (disabled for local dev)
USE_S3=False
AWS_STORAGE_BUCKET_NAME=qu-security-static
AWS_S3_REGION_NAME=us-east-2
EOF
    echo "✅ Created .env file for local development"
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
