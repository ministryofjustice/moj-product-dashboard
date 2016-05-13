#!/usr/bin/env bash
set -e

# Run migrations if there are any
/app/venv/bin/python manage.py migrate --settings dashboard.settings.base

# Run server
/usr/local/bin/uwsgi --ini /app/conf/uwsgi.ini
