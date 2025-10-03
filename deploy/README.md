# QU Security Backend - Docker Deployment

This directory contains Docker configuration files for running the QU Security Backend application with all its dependencies.

## Services Included

- **PostgreSQL 15** - Primary database
- **Redis 7** - Caching and session storage
- **RabbitMQ 3.12** - Message broker for Celery tasks
- **Memcached 1.6** - Additional caching layer
- **Nginx** - Reverse proxy and static file server
- **Django Web App** - Main application server
- **Celery Worker** - Background task processor
- **Celery Beat** - Periodic task scheduler

## Quick Start

1. **Navigate to the deploy directory:**
   ```bash
   cd deploy
   ```

2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Django API: http://localhost:8000
   - Through Nginx: http://localhost:80
   - RabbitMQ Management: http://localhost:15672 (admin/admin)
   - PostgreSQL: localhost:5432

## Environment Configuration

The setup uses environment variables defined in the `docker-compose.yml` file. For production deployment, create a `.env` file in this directory with your custom values:

```bash
cp .env.docker .env
# Edit .env with your production values
```

## Available Commands

### Start services in background:
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f postgres
```

### Run Django management commands:
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Django shell
docker-compose exec web python manage.py shell
```

### Database operations:
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d qu_security_db

# Create database backup
docker-compose exec postgres pg_dump -U postgres qu_security_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres qu_security_db < backup.sql
```

### Monitor Celery tasks:
```bash
# Connect to RabbitMQ management interface
# URL: http://localhost:15672
# Username: qu_user
# Password: qu_password

# Monitor Celery worker
docker-compose exec celery celery -A qu_security inspect active
```

## Development Workflow

### For development with live code reloading:
1. The `docker-compose.yml` mounts your local code directory into the container
2. The Django development server automatically reloads on code changes
3. Static files and templates are served by Django in debug mode

### Production Deployment

For production deployment, make the following changes:

1. **Update environment variables:**
   ```bash
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_PASSWORD=strong-production-password
   ```

2. **Enable SSL/TLS:**
   ```bash
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

3. **Configure S3 for static/media files:**
   ```bash
   USE_S3=True
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_STORAGE_BUCKET_NAME=your-bucket
   ```

4. **Use Gunicorn instead of runserver:**
   Update the web service command in `docker-compose.yml`:
   ```yaml
   command: gunicorn --bind 0.0.0.0:8000 --workers 4 qu_security.wsgi:application
   ```

## Service Configuration

### PostgreSQL
- **Database:** qu_security_db
- **Username:** postgres
- **Password:** postgres (change in production)
- **Port:** 5432

### Redis
- **Host:** redis
- **Port:** 6379
- **Database 0:** General cache
- **Database 1:** Celery results

### RabbitMQ
- **Host:** rabbitmq
- **Port:** 5672 (AMQP), 15672 (Management)
- **Username:** qu_user
- **Password:** qu_password
- **Virtual Host:** /

### Memcached
- **Host:** memcached
- **Port:** 11211
- **Memory:** 64MB

## Volumes and Data Persistence

The following Docker volumes are created for data persistence:
- `postgres_data` - PostgreSQL database files
- `redis_data` - Redis data files
- `rabbitmq_data` - RabbitMQ data files
- `static_volume` - Django static files
- `media_volume` - User uploaded media files

## Networking

All services are connected via the `qu_security_network` bridge network, allowing them to communicate using service names as hostnames.

## Health Checks

Health checks are configured for:
- PostgreSQL: `pg_isready` command
- Redis: `redis-cli ping`
- RabbitMQ: Port connectivity check
- Django app: HTTP health check on admin endpoint

## Scaling

To scale services horizontally:

```bash
# Scale web workers
docker-compose up --scale web=3

# Scale Celery workers
docker-compose up --scale celery=2
```

## Troubleshooting

### Common Issues:

1. **Database connection errors:**
   - Ensure PostgreSQL service is healthy: `docker-compose ps`
   - Check logs: `docker-compose logs postgres`

2. **Celery tasks not processing:**
   - Check RabbitMQ status: `docker-compose logs rabbitmq`
   - Monitor Celery worker: `docker-compose logs celery`

3. **Static files not loading:**
   - Run collectstatic: `docker-compose exec web python manage.py collectstatic`
   - Check Nginx configuration and volume mounts

4. **Memory issues:**
   - Increase Docker memory allocation
   - Monitor container resource usage: `docker stats`

### Logs and Debugging:

```bash
# View all logs
docker-compose logs -f

# Debug specific service
docker-compose exec web bash
docker-compose exec postgres bash

# Monitor resource usage
docker-compose top
```

## Security Considerations

For production deployment:

1. Change all default passwords
2. Use environment files with restricted permissions
3. Enable SSL/TLS termination
4. Configure firewall rules
5. Regular security updates
6. Monitor logs for suspicious activity
7. Use secrets management for sensitive data

## Backup Strategy

1. **Database backups:**
   ```bash
   docker-compose exec postgres pg_dump -U postgres qu_security_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
   ```

2. **Media files backup:**
   ```bash
   docker cp qu_security_web:/app/media ./media_backup
   ```

3. **Automated backups:**
   Set up cron jobs or use backup solutions like AWS EBS snapshots for persistent volumes.