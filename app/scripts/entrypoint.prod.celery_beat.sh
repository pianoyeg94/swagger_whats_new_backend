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

celery -A config beat --scheduler=django_celery_beat.schedulers:DatabaseScheduler --loglevel=debug

exec "$@"