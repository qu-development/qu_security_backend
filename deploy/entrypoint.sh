#!/bin/sh
python3 manage.py migrate

mkdir -p /var/log/celery/

python3 -m celery  -A qu_security beat --logfile=/var/log/celery/beat.log --loglevel=info --pidfile=/tmp/celeryworker.pid --schedule=/tmp/celerybeat-schedule --detach
python3 -m celery  -A qu_security worker --logfile=/var/log/celery/worker.log --loglevel=info --pidfile=/tmp/celerybeat.pid --schedule=/tmp/celerybeat-worker --detach

python3 manage.py collectstatic --noinput

python3 -m gunicorn qu_security.wsgi:application --bind :8000 --workers 4 --timeout 120
