#!/bin/bash

# Script to run database migrations

echo "🔄 Running RaGenie Database Migrations"
echo "========================================"
echo ""

# Check if Docker Compose is running
if ! docker-compose ps | grep -q "postgres.*Up"; then
    echo "❌ PostgreSQL is not running!"
    echo "Please start services with: docker-compose up -d postgres"
    exit 1
fi

echo "✓ PostgreSQL is running"
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
timeout=30
elapsed=0

while ! docker-compose exec -T postgres pg_isready -U ragenie > /dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ PostgreSQL did not become ready in time"
        exit 1
    fi
    sleep 1
    ((elapsed++))
    echo -n "."
done

echo ""
echo "✓ PostgreSQL is ready"
echo ""

# Run migrations
echo "Running Alembic migrations..."
cd "$(dirname "$0")/.." || exit

# Set environment variable for database URL
export DATABASE_URL=${DATABASE_URL:-"postgresql://ragenie:ragenie_dev_password@localhost:5432/ragenie"}

# Run migration
cd migrations || exit
alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migrations completed successfully!"
    echo ""
    echo "Database schema is now up to date."
else
    echo ""
    echo "❌ Migration failed!"
    echo "Check the error messages above."
    exit 1
fi
