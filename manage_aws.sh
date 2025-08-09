#!/bin/bash

# Management commands for AWS Lambda deployment

echo "QU Security Backend - AWS Management Commands"
echo "=============================================="

if [ -z "$1" ]; then
    echo "Usage: $0 [command]"
    echo ""
    echo "Available commands:"
    echo "  migrate         - Run database migrations"
    echo "  collectstatic   - Collect static files"
    echo "  createsuperuser - Create Django superuser"
    echo "  shell           - Open Django shell"
    echo "  logs            - View Lambda logs"
    echo "  status          - Show deployment status"
    echo "  update-env      - Update environment variables"
    echo ""
    exit 1
fi

ENVIRONMENT=${2:-dev}

case "$1" in
    migrate)
        echo "Running migrations on $ENVIRONMENT..."
        zappa manage $ENVIRONMENT migrate
        ;;
    collectstatic)
        echo "Collecting static files on $ENVIRONMENT..."
        zappa manage $ENVIRONMENT "collectstatic --noinput"
        ;;
    createsuperuser)
        echo "Creating superuser on $ENVIRONMENT..."
        zappa manage $ENVIRONMENT createsuperuser
        ;;
    shell)
        echo "Opening Django shell on $ENVIRONMENT..."
        zappa manage $ENVIRONMENT shell
        ;;
    logs)
        echo "Viewing logs for $ENVIRONMENT..."
        zappa tail $ENVIRONMENT
        ;;
    status)
        echo "Deployment status for $ENVIRONMENT..."
        zappa status $ENVIRONMENT
        ;;
    update-env)
        echo "Updating environment variables for $ENVIRONMENT..."
        echo "Note: You need to manually update zappa_settings.json and run 'zappa update $ENVIRONMENT'"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0' without arguments to see available commands."
        exit 1
        ;;
esac
