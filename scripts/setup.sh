#!/usr/bin/env bash
# FAIR Data Demo — One-shot setup script
# Converts source data, builds containers, migrates DB, imports XML, initializes GraphDB.

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

# Step 1: Convert source data (if source_data has files)
NHANES_FILES=$(find "$PROJECT_DIR/source_data/nhanes" -name "*.XPT" -o -name "*.xpt" -o -name "*.csv" 2>/dev/null | head -1)
ADNI_FILES=$(find "$PROJECT_DIR/source_data/adni" -name "*.csv" 2>/dev/null | head -1)
SPRINT_FILES=$(find "$PROJECT_DIR/source_data/sprint" -name "*.csv" 2>/dev/null | head -1)

if [ -n "$NHANES_FILES" ] || [ -n "$ADNI_FILES" ] || [ -n "$SPRINT_FILES" ]; then
    echo ""
    echo "Step 1: Converting source data to XML..."
    python "$PROJECT_DIR/datagen/convert_all.py"
else
    echo ""
    echo "Step 1: No source data found. Skipping conversion."
    echo "  See source_data/README.md for download instructions."
fi

# Step 2: Build and start Docker services
echo ""
echo "Step 2: Building and starting Docker services..."
cd "$PROJECT_DIR"
docker compose build
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services..."
sleep 10

# Step 3: Run Django migrations
echo ""
echo "Step 3: Running database migrations..."
docker compose exec web python manage.py migrate --noinput

# Step 4: Create superuser (if not exists)
echo ""
echo "Step 4: Creating admin user..."
docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin / admin')
else:
    print('Superuser already exists.')
"

# Step 5: Initialize GraphDB
echo ""
echo "Step 5: Initializing GraphDB repository..."
docker compose exec web python manage.py init_graphdb

# Step 6: Import XML data (if available)
IMPORT_FILES=$(find "$PROJECT_DIR/app/import_data" -name "*.xml" 2>/dev/null | head -1)
if [ -n "$IMPORT_FILES" ]; then
    echo ""
    echo "Step 6: Importing XML instance data..."
    # TODO: Run bulk import command when study apps are generated
    echo "  Import command will be available after study apps are generated."
else
    echo ""
    echo "Step 6: No XML data to import. Generate models in SDCStudio first."
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
echo "  1. Download source data (see source_data/README.md)"
echo "  2. Generate study models in SDCStudio"
echo "  3. Run datagen/convert_all.py to create XML instances"
echo "  4. Import data and explore cross-study queries"
