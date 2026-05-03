#!/bin/sh
echo "Starting application..."
echo "PORT is set to: $PORT"
echo "Current directory: $(pwd)"
echo "Listing files in current directory:"
ls -R
echo "Listing files in /keys:"
ls -R /keys || echo "/keys directory not found"

# Default port to 8080 for Cloud Run
export PORT=${PORT:-8080}

echo "Starting uvicorn on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
