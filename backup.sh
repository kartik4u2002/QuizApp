#!/usr/bin/env bash
# Automated Backup Script for Quiz Platform

set -e

# Configuration
BACKUP_DIR="/var/backups/quiz-platform"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")

echo "=== Starting Backup: $TIMESTAMP ==="

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if docker-compose file is present
if [ ! -f docker-compose.production.yml ]; then
  echo "Error: docker-compose.production.yml not found in $SCRIPT_DIR."
  exit 1
fi

# 1. Backup MongoDB database using mongodump
echo "Backing up MongoDB database..."
set +e
docker compose -f docker-compose.production.yml exec -T mongodb mongodump --archive --gzip > "$BACKUP_DIR/mongodb_$TIMESTAMP.gz"
MONGO_STATUS=$?
set -e

if [ $MONGO_STATUS -ne 0 ]; then
  echo "Error: MongoDB backup failed!"
  # Clean up partial file
  rm -f "$BACKUP_DIR/mongodb_$TIMESTAMP.gz"
  exit 1
fi

# 2. Backup Django SQLite database (if it exists)
SQLITE_PATH="./django_backend/db.sqlite3"
if [ -f "$SQLITE_PATH" ]; then
  echo "Backing up Django SQLite database..."
  cp "$SQLITE_PATH" "$BACKUP_DIR/django_sqlite_$TIMESTAMP.db"
else
  echo "No SQLite database found at $SQLITE_PATH (skipping Django DB backup)."
fi

# 3. Create a unified compressed tar archive
echo "Packaging backup files..."
cd "$BACKUP_DIR"
TAR_FILE="quiz_platform_backup_$TIMESTAMP.tar.gz"

# Add whatever files were successfully generated
FILES_TO_PACK=()
[ -f "mongodb_$TIMESTAMP.gz" ] && FILES_TO_PACK+=("mongodb_$TIMESTAMP.gz")
[ -f "django_sqlite_$TIMESTAMP.db" ] && FILES_TO_PACK+=("django_sqlite_$TIMESTAMP.db")

if [ ${#FILES_TO_PACK[@]} -gt 0 ]; then
  tar -czf "$TAR_FILE" "${FILES_TO_PACK[@]}"
  
  # Clean up intermediate files
  rm -f "${FILES_TO_PACK[@]}"
  
  echo "Backup saved successfully as: $BACKUP_DIR/$TAR_FILE"
  echo "Archive size: $(du -sh "$TAR_FILE" | cut -f1)"
else
  echo "Error: No files were available to package!"
  exit 1
fi

# 4. Enforce Retention Policy (Clean up backups older than RETENTION_DAYS)
echo "Enforcing retention policy (deleting backups older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -name "quiz_platform_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "=== Backup Process Completed Successfully ==="
