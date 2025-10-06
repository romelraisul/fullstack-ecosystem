#!/bin/bash
#
# This script waits for all the Docker Compose services to be healthy.
#
# Usage: ./wait-for-services.sh
#

# Set the timeout in seconds
timeout=120
interval=5
end_time=$((SECONDS + timeout))

while [ $SECONDS -lt $end_time ]; do
  unhealthy_services=$(docker compose ps | grep -c "unhealthy")
  if [ "$unhealthy_services" -eq 0 ]; then
    echo "All services are healthy."
    exit 0
  fi
  echo "Waiting for services to become healthy..."
  sleep $interval
done

echo "Error: Timed out waiting for services to become healthy."
docker compose ps
exit 1
