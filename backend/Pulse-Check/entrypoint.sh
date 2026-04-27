#!/bin/sh

# Run Database Migrations
echo "Applying database migrations..."
python manage.py migrate

# Execute the CMD from Dockerfile or docker-compose
exec "$@"
