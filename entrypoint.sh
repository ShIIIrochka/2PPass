#!/bin/ash

./manage.py migrate
./manage.py collectstatic --noinput
gunicorn --bind ${APP_HOST}:${APP_PORT} config.wsgi:application
