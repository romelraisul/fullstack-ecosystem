#!/usr/bin/env bash
set -euo pipefail

# Uptime checker for Hostamar
# Env: HEALTH_URL (default: https://hostamar.com/api/health)
#      LOG_FILE (default: /var/log/hostamar/uptime_check.log)

HEALTH_URL="${HEALTH_URL:-https://hostamar.com/api/health}"
LOG_FILE="${LOG_FILE:-/var/log/hostamar/uptime_check.log}"

mkdir -p "$(dirname "$LOG_FILE")"

TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Capture body and trailing line with code/time in a single call
OUT="$(curl -sS --max-time 10 -w '\n%{http_code} %{time_total}\n' "$HEALTH_URL" || true)"
CODE_TIME_LINE="$(printf "%s" "$OUT" | tail -n 1)"
BODY="$(printf "%s" "$OUT" | sed '$d')"
HTTP_CODE="$(awk '{print $1}' <<<"$CODE_TIME_LINE")"
TOTAL_TIME="$(awk '{print $2}' <<<"$CODE_TIME_LINE")"

if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "$TS | UPTIME | FAIL | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL}" >> "$LOG_FILE"
  exit 1
fi

if ! grep -qi '"status"\s*:\s*"ok"' <<<"$BODY"; then
  echo "$TS | UPTIME | WARN | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL} body_missing_status_ok" >> "$LOG_FILE"
  exit 0
fi

echo "$TS | UPTIME | OK | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL}" >> "$LOG_FILE"