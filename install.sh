#!/bin/bash

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install package in development mode
echo "Installing package..."
pip install -e ".[dev]"

# Create necessary directories
mkdir -p logs
mkdir -p trigger_actions

# Start the Celery worker in the background
echo "Starting Celery worker..."
export TRIGGERED_START_WORKER=false  # Disable worker in server
celery -A triggered.queue worker --loglevel=INFO --concurrency=1 --pool=solo > logs/celery.log 2>&1 &
CELERY_PID=$!

# Start the server
echo "Starting server..."
triggered start

# Cleanup on exit
trap "kill $CELERY_PID" EXIT 