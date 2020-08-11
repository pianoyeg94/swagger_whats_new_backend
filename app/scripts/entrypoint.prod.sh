#!/bin/sh

echo "Waiting for Postgres..."

while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 0.1
done

echo "Postgres started"

echo "Waiting for RabbitMQ..."

while ! nc -z $BROKER_HOST $BROKER_PORT; do
  sleep 0.1
done

echo "RabbitMQ started"

python manage.py collectstatic --no-input --clear
gunicorn --workers=$(( 2 * `cat /proc/cpuinfo | grep 'core id' | wc -l` + 1 )) \
 --bind=0.0.0.0:8000 --log-level=error wsgi:application

exec "$@"