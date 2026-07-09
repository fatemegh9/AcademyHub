#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt

echo "=== DEBUG: Current directory ==="
pwd
echo "=== DEBUG: Root files ==="
ls -la
echo "=== DEBUG: static folder content ==="
ls -la static/
echo "=== DEBUG: static/css content ==="
ls -la static/css/ 2>&1 || echo "static/css NOT FOUND"

python manage.py collectstatic --no-input
python manage.py migrate