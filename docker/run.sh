#!/usr/bin/env bash
set -e

# Run migrations if there are any
/usr/bin/python3 manage.py migrate --run-syncdb --settings dashboard.settings.base --noinput

# Load fixtures
/usr/bin/python3 manage.py loaddata auth_group_permissions

# Create finance admin user if not exists
/usr/bin/python3 manage.py ensure_finance_admin_user

# Run server
/usr/local/bin/uwsgi --http-socket :$1 --pythonpath /usr/bin/python3 --ini /app/conf/uwsgi.ini
