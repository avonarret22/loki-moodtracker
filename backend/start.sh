#!/bin/bash
set -e

echo "========================================="
echo "Starting Loki Mood Tracker"
echo "========================================="

echo "[1/4] Cleaning up old database (if needed)..."
cd /app/backend
bash cleanup_db.sh

echo "[2/4] Running Alembic migrations..."
alembic upgrade head

echo "[3/4] Migrations completed successfully"

echo "[4/4] Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
