#!/usr/bin/env bash
set -e

/usr/bin/python manage.py migrate prototype --fake --settings dashboard.settings.base --noinput

# Run migrations if there are any
/usr/bin/python manage.py migrate --fake-initial --run-syncdb --settings dashboard.settings.base --noinput

# Load fixtures
/usr/bin/python manage.py loaddata auth_group_permissions

# Run server
/usr/local/bin/uwsgi --ini /app/conf/uwsgi.ini
