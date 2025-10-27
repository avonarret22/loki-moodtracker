#!/bin/bash
# Script to clean up old database before running migrations
# This ensures a fresh start with the merged migration

echo "🧹 Cleaning up old database..."

if [ -f "./data/moodtracker.db" ]; then
    echo "   Removing existing database file..."
    rm -f ./data/moodtracker.db
    echo "   ✓ Database file removed"
else
    echo "   No existing database file found (this is fine)"
fi

if [ -d "./data" ]; then
    echo "   ✓ Data directory exists"
else
    echo "   Creating data directory..."
    mkdir -p ./data
    echo "   ✓ Data directory created"
fi

echo "🧹 Cleanup complete!"
