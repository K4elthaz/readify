#!/bin/sh

# Run Django makemigrations and migrate
python manage.py makemigrations
python manage.py migrate

# Start the Django server
# Using `runserver` in development; change to `gunicorn` or other WSGI server for production
python manage.py runserver 0.0.0.0:8000 &
# Start the Celery worker
celery -A blendjoy worker --loglevel=info --pool=eventlet