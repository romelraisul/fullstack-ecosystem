#!/usr/bin/env bash
# Simple health-check script for local infra (Ollama, MCP, Unified backend, Grafana, Prometheus)
# Places: Automations/infrastructure
# Usage: sudo bash health_check.sh [host]

set -euo pipefail

HOST=${1:-localhost}
TIMEOUT=${2:-3}

services=(
  "ollama|$HOST|11434|/"
  "mcp-server|$HOST|8080|/"
  "unified-backend|$HOST|8011|/health"
  "grafana|$HOST|3000|/"
  "prometheus|$HOST|9090|/"
)

command_exists(){ command -v "$1" >/dev/null 2>&1; }

check_http(){
  local host=$1; local port=$2; local path=$3
  local url="http://${host}:${port}${path}"
  if command_exists curl; then
    if curl --silent --show-error --fail --max-time $TIMEOUT "$url" >/dev/null 2>&1; then
      return 0
    else
      return 1
    fi
  elif command_exists wget; then
    if wget -q --timeout=$TIMEOUT --spider "$url" >/dev/null 2>&1; then
      return 0
    else
      return 1
    fi
  else
    # fallback to /dev/tcp if available
    if (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; then
      return 0
    else
      return 1
    fi
  fi
}

down=()
for svc in "${services[@]}"; do
  IFS='|' read -r name host port path <<< "$svc"
  path=${path:-/}
  if check_http "$host" "$port" "$path"; then
    printf "%-16s OK\n" "$name"
  else
    printf "%-16s DOWN\n" "$name"
    down+=($name)
  fi
done

if [ ${#down[@]} -eq 0 ]; then
  echo "OK: all services healthy"
  exit 0
else
  echo "WARN: services down: ${down[*]}"
  exit 2
fi
