#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt

echo "=== DEBUG: Django static settings ==="
python manage.py shell -c "from django.conf import settings; print('STATICFILES_DIRS:', settings.STATICFILES_DIRS); print('STATIC_ROOT:', settings.STATIC_ROOT); print('BASE_DIR:', settings.BASE_DIR)"

echo "=== DEBUG: findstatic test ==="
python manage.py findstatic css/base.css -v2

python manage.py collectstatic --no-input
python manage.py migrate