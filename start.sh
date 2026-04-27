#!/bin/bash
set -e

if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example and fill in values."
    exit 1
fi

export $(grep -v '^#' .env | xargs)

source venv/bin/activate

uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
