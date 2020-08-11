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

celery worker -A config --loglevel=debug --pool=gevent --concurrency=10

exec "$@"