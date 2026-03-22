#!/usr/bin/env bash
# FAIR Data Demo — One-shot setup script
# Builds containers, migrates DB, initializes GraphDB.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== FAIR Data Demo Setup ==="
echo ""

# Check for .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Creating .env from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "Edit .env if you need to change defaults."
fi

# Step 1: Build and start Docker services
echo ""
echo "Step 1: Building and starting Docker services..."
cd "$PROJECT_DIR"
docker compose build
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services..."
sleep 10

# Step 2: Run Django migrations
echo ""
echo "Step 2: Running database migrations..."
docker compose exec web python manage.py migrate --noinput

# Step 3: Create superuser (if not exists)
echo ""
echo "Step 3: Creating admin user..."
docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin / admin')
else:
    print('Superuser already exists.')
"

# Step 4: Initialize GraphDB
echo ""
echo "Step 4: Initializing GraphDB repository..."
docker compose exec web python manage.py init_graphdb

# Step 5: Import XML data (if available)
IMPORT_FILES=$(find "$PROJECT_DIR/app/import_data" -name "*.xml" 2>/dev/null | head -1)
if [ -n "$IMPORT_FILES" ]; then
    echo ""
    echo "Step 5: Importing XML instance data..."
    # TODO: Run bulk import command when study apps are generated
    echo "  Import command will be available after study apps are generated."
else
    echo ""
    echo "Step 5: No XML data to import. Generate models in SDCStudio first."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services:"
echo "  Django:         http://localhost:${WEB_PORT:-8000}"
echo "  Django Admin:   http://localhost:${WEB_PORT:-8000}/admin  (admin / admin)"
echo "  GraphDB:        http://localhost:${GRAPHDB_PORT:-7200}"
echo ""
echo "Next steps:"
echo "  1. Upload Markdown templates (templates/*.md) to the FAIR Data Demo project in SDCStudio"
echo "  2. SDCStudio assembles models, reusing existing NIH-CDE catalog components"
echo "  3. Generate apps and export all 8 output formats"
echo "  4. Add generated output to models/ directory in this repo"
echo "  5. Download source data (see source_data/README.md)"
echo "  6. Run datagen/ converters to create XML instances"
echo "  7. Import data and explore cross-study queries"
