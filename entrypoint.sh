#!/bin/sh
echo "Starting application..."
echo "PORT is set to: $PORT"
echo "Current directory: $(pwd)"
echo "Listing files in current directory:"
ls -R
echo "Listing files in /keys:"
ls -R /keys || echo "/keys directory not found"

if [ -n "$K_SERVICE" ]; then
  echo "Running on Cloud Run: $K_SERVICE"
  export PORT=${PORT:-8080}
else
  echo "Running locally"
  export PORT=${PORT:-8000}
fi

echo "Starting Temporal Worker..."
python3 temporal_worker.py &

echo "Starting uvicorn on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
