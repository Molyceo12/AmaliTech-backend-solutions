#!/bin/sh

# Run Database Migrations
echo "Applying database migrations..."
python manage.py migrate

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn idempotency_gateway.wsgi:application --bind 0.0.0.0:${PORT:-8000}
