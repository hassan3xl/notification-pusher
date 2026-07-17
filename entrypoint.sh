#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# 0. Check production environment database override
if [ "$FASTAPI_ENV" = "production" ]; then
  echo "Production environment detected."
  if [ -n "$PRODUCTION_DB" ]; then
    export DATABASE_URL="$PRODUCTION_DB"
    echo "Using PRODUCTION_DB database URL."
  fi
fi

# 1. Parse and wait for database
if [ -n "$DATABASE_URL" ]; then
  # Strip protocol prefix (postgresql:// or postgres://)
  STRIPPED_URL=$(echo $DATABASE_URL | sed -e 's/postgresql:\/\///' -e 's/postgres:\/\///')
  # Extract connection part after user:pass (if @ is present)
  if [[ "$STRIPPED_URL" == *"@"* ]]; then
    HOST_PORT=$(echo $STRIPPED_URL | sed -e 's/.*@//' -e 's/\/.*//')
  else
    HOST_PORT=$(echo $STRIPPED_URL | sed -e 's/\/.*//')
  fi
  # Strip query parameters (like ?sslmode=require)
  HOST_PORT=$(echo $HOST_PORT | cut -d? -f1)
  
  DB_HOST=$(echo $HOST_PORT | cut -d: -f1)
  DB_PORT=$(echo $HOST_PORT | cut -d: -f2)
  # Default to 5432 if no port is specified in connection string
  if [ "$DB_HOST" = "$HOST_PORT" ]; then
    DB_PORT=5432
  fi
fi

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

echo "Waiting for Database at $DB_HOST:$DB_PORT..."
if command -v nc >/dev/null 2>&1; then
  while ! nc -z $DB_HOST $DB_PORT; do
    echo "Database not ready, waiting..."
    sleep 1
  done
else
  echo "nc not found, sleeping for 3s..."
  sleep 3
fi
echo "Database is ready!"

# 2. Wait for Redis
if [ -n "$REDIS_URL" ]; then
  REDIS_HOST=$(echo $REDIS_URL | sed -e 's/redis:\/\///' -e 's/:.*//' -e 's/\/.*//')
  REDIS_PORT=$(echo $REDIS_URL | sed -e 's/.*://' -e 's/\/.*//')
fi
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
if command -v nc >/dev/null 2>&1; then
  while ! nc -z $REDIS_HOST $REDIS_PORT; do
    echo "Redis not ready, waiting..."
    sleep 1
  done
else
  echo "nc not found, sleeping for 3s..."
  sleep 3
fi
echo "Redis is ready!"

# 3. Start Application
if [ "$FASTAPI_ENV" = "production" ]; then
  echo "Running in PRODUCTION mode"
  exec uv run uvicorn main:socket_app \
      --host 0.0.0.0 \
      --port ${PORT:-8000} \
      --workers ${WORKERS:-4}
else
  echo "Running in DEVELOPMENT mode"
  exec uv run uvicorn main:socket_app \
      --host 0.0.0.0 \
      --port 8000 \
      --reload
fi