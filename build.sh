#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd core
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --no-input 2>/dev/null || true
