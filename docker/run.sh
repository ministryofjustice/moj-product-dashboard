#!/usr/bin/env bash
set -e

# Run migrations if there are any
/usr/bin/python3 manage.py migrate --fake-initial --run-syncdb --settings dashboard.settings.base --noinput

# Load fixtures
/usr/bin/python3 manage.py loaddata auth_group_permissions

# Run server
/usr/local/bin/uwsgi --ini /app/conf/uwsgi.ini
