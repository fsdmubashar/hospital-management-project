#!/usr/bin/env bash
set -euo pipefail

echo "Preparing local runtime directories..."
mkdir -p logs backups reports_output mysql_data postgres_data
touch hospital.db
chmod 600 hospital.db || true

if [ -S /tmp/.X11-unix/X0 ] || [ -d /tmp/.X11-unix ]; then
  ln -sfn /tmp/.X11-unix ./.x11-unix
fi

if [ ! -f .env ]; then
  echo "No .env file detected. Continuing with environment defaults."
fi

echo "Building Docker image..."
docker compose build

echo "Initializing database and seed data..."
docker compose run --rm hospital-app true

echo "Setup complete."
echo "For Linux GUI containers, ensure host X11 access is enabled:"
echo "  xhost +local:docker"
echo "Start application with:"
echo "  docker compose up"
