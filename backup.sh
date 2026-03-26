#!/bin/bash
# Database Backup Script
CONTAINER_NAME=$(docker-compose ps -q db)
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Backing up database..."
docker exec -t $CONTAINER_NAME pg_dumpall -c -U postgres > $BACKUP_FILE
gzip $BACKUP_FILE
echo "Backup created: ${BACKUP_FILE}.gz"
