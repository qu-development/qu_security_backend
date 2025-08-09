#!/bin/bash

# Deployment script for AWS Lambda using Zappa

echo "Starting deployment to AWS Lambda..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files (if needed locally)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if this is the first deployment
if [ "$1" = "init" ]; then
    echo "Initializing first deployment..."
    zappa deploy dev
else
    echo "Updating existing deployment..."
    zappa update dev
fi

echo "Deployment completed!"
echo "Don't forget to:"
echo "1. Set up your RDS database"
echo "2. Run migrations: zappa manage dev migrate"
echo "3. Create superuser: zappa manage dev createsuperuser"
echo "4. Configure your S3 bucket permissions"
