#!/bin/bash
set -euo pipefail

# Start the backend in the background
echo "Starting backend..."
(cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000) &

# Start the frontend development server
echo "Starting frontend..."
(cd frontend && npm run dev) &

# Wait for all background processes to finish
wait