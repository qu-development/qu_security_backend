# QU Security Backend - Docker Management Makefile

# Default target
.DEFAULT_GOAL := help

# Variables
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := qu_security

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

.PHONY: help build up down restart logs shell migrate createsuperuser collectstatic test clean backup restore

help: ## Show this help message
	@echo "$(BLUE)QU Security Backend - Docker Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build or rebuild services
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all services in the background
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started! Access the app at http://localhost:8000$(NC)"

up-build: ## Build and start all services
	@echo "$(BLUE)Building and starting all services...$(NC)"
	docker-compose up --build -d
	@echo "$(GREEN)Services started! Access the app at http://localhost:8000$(NC)"

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	docker-compose restart

stop: ## Stop all services without removing containers
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose stop

logs: ## Show logs for all services
	docker-compose logs -f

logs-web: ## Show logs for web service only
	docker-compose logs -f web

logs-celery: ## Show logs for celery service only
	docker-compose logs -f celery

logs-db: ## Show logs for postgres service only
	docker-compose logs -f postgres

shell: ## Open Django shell in web container
	docker-compose exec web python manage.py shell

bash: ## Open bash shell in web container
	docker-compose exec web bash

db-shell: ## Connect to PostgreSQL database
	docker-compose exec postgres psql -U postgres -d qu_security_db

migrate: ## Run Django migrations
	@echo "$(BLUE)Running Django migrations...$(NC)"
	docker-compose exec web python manage.py migrate

makemigrations: ## Create new Django migrations
	@echo "$(BLUE)Creating Django migrations...$(NC)"
	docker-compose exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	@echo "$(BLUE)Creating Django superuser...$(NC)"
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	@echo "$(BLUE)Collecting static files...$(NC)"
	docker-compose exec web python manage.py collectstatic --noinput

test: ## Run Django tests
	@echo "$(BLUE)Running Django tests...$(NC)"
	docker-compose exec web python manage.py test

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker-compose exec web coverage run --source='.' manage.py test
	docker-compose exec web coverage report
	docker-compose exec web coverage html

lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	docker-compose exec web ruff check .
	docker-compose exec web ruff format --check .

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	docker-compose exec web ruff format .

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	docker-compose exec web bandit -r . -f json

ps: ## Show running containers
	docker-compose ps

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"

clean: ## Remove containers, networks, and volumes
	@echo "$(YELLOW)Warning: This will remove all containers, networks, and volumes!$(NC)"
	@echo "$(RED)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Remove everything including images
	@echo "$(YELLOW)Warning: This will remove containers, networks, volumes, and images!$(NC)"
	@echo "$(RED)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

backup-db: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U postgres qu_security_db | gzip > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)Database backup created in backups/ directory$(NC)"

restore-db: ## Restore database from backup (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Please specify BACKUP_FILE: make restore-db BACKUP_FILE=backups/backup_file.sql.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Warning: This will replace the current database!$(NC)"
	@echo "$(RED)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	@echo "$(BLUE)Restoring database from $(BACKUP_FILE)...$(NC)"
	gunzip -c $(BACKUP_FILE) | docker-compose exec -T postgres psql -U postgres qu_security_db
	@echo "$(GREEN)Database restored successfully$(NC)"

backup-media: ## Backup media files
	@echo "$(BLUE)Backing up media files...$(NC)"
	@mkdir -p backups
	docker-compose exec web tar -czf - /app/media | cat > backups/media_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz
	@echo "$(GREEN)Media backup created in backups/ directory$(NC)"

init: ## Initialize the project (first-time setup)
	@echo "$(BLUE)Initializing QU Security Backend...$(NC)"
	make build
	make up
	@echo "$(BLUE)Waiting for services to start...$(NC)"
	sleep 10
	make migrate
	@echo "$(GREEN)Project initialized! You can now create a superuser with 'make createsuperuser'$(NC)"

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up --build

prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	docker-compose -f docker-compose.yml up --build -d

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker-compose ps | grep -E "(Up|healthy)" && echo "$(GREEN)Services are healthy$(NC)" || echo "$(RED)Some services are unhealthy$(NC)"

monitor: ## Show resource usage
	@echo "$(BLUE)Container resource usage:$(NC)"
	docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

update: ## Update and restart services
	@echo "$(BLUE)Updating services...$(NC)"
	docker-compose pull
	make down
	make up-build
	@echo "$(GREEN)Services updated and restarted$(NC)"

# Help with environment setup
env-help: ## Show environment variable help
	@echo "$(BLUE)Environment Configuration Help:$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  Copy and customize .env.docker to .env for local overrides"
	@echo ""
	@echo "$(GREEN)Production:$(NC)"
	@echo "  Set these important variables:"
	@echo "    DEBUG=False"
	@echo "    SECRET_KEY=your-production-secret"
	@echo "    ALLOWED_HOSTS=yourdomain.com"
	@echo "    DB_PASSWORD=strong-password"
	@echo "    USE_S3=True (for production static files)"
	@echo ""
	@echo "$(GREEN)AWS S3 Configuration:$(NC)"
	@echo "    AWS_ACCESS_KEY_ID=your-key"
	@echo "    AWS_SECRET_ACCESS_KEY=your-secret"
	@echo "    AWS_STORAGE_BUCKET_NAME=your-bucket"