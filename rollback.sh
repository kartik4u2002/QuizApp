#!/usr/bin/env bash
# Rollback Script for Quiz Platform

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (using sudo)."
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Target revision: defaults to the previous commit (HEAD@{1}) or first argument
TARGET_REF="${1:-HEAD@{1}}"

echo "=== Initiating Rollback ==="
echo "Rolling back to Git reference: $TARGET_REF"

# Verify git repository exists
if [ ! -d .git ]; then
  echo "Error: Not a Git repository. Cannot perform rollback."
  exit 1
fi

# Fetch current commit to show where we are reverting from
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Reverting from current commit: $CURRENT_COMMIT"

# Reset git to the target ref
git checkout "$TARGET_REF"
REVERTED_COMMIT=$(git rev-parse HEAD)
echo "Checked out commit: $REVERTED_COMMIT"

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

DOMAIN="${DOMAIN:-localhost}"

# Rebuild and restart containers
echo "Rebuilding and restarting services..."
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d

# Run database operations
echo "Running migrations and static collection..."
docker compose -f docker-compose.production.yml exec -T django_backend python manage.py migrate --noinput
docker compose -f docker-compose.production.yml exec -T django_backend python manage.py collectstatic --noinput

# Verify health status
echo "Verifying service health..."
sleep 5

# Check Nginx / Django Health Check
set +e
DJANGO_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/)
FASTAPI_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
set -e

echo "Django Container Health HTTP Status: $DJANGO_HEALTH"
echo "FastAPI Container Health HTTP Status: $FASTAPI_HEALTH"

if [ "$DJANGO_HEALTH" = "200" ] && [ "$FASTAPI_HEALTH" = "200" ]; then
  echo "=== Rollback Completed Successfully and Verified ==="
else
  echo "WARNING: Rollback completed but one or more health checks failed!"
  echo "Django Status (expected 200): $DJANGO_HEALTH"
  echo "FastAPI Status (expected 200): $FASTAPI_HEALTH"
  exit 1
fi
