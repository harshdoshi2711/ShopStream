#!/bin/sh
set -e

echo "⏳ Waiting for database..."
scripts/wait-for-db.sh

echo "📦 Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting application..."
exec "$@"
