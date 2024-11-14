@echo off

REM Install requirements
pip install -r requirements.txt

REM Run Django makemigrations
python manage.py makemigrations

REM Run Django migrate
python manage.py migrate

REM Run Django runserver and Celery worker simultaneously
start cmd /k python manage.py runserver
start cmd /k python celery_worker.py -A blendjoy worker --loglevel=info --pool=eventlet

REM Note: This script doesn't wait for the processes to finish.
REM They will run in separate command windows.