#!/bin/bash
set -e

echo "========================================="
echo "Starting Loki Mood Tracker"
echo "========================================="

echo "[1/3] Running Alembic migrations..."
cd /app/backend
alembic upgrade head

echo "[2/3] Migrations completed successfully"

echo "[3/3] Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
