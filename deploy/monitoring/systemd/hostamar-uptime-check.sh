#!/usr/bin/env bash
set -euo pipefail

# Uptime checker for Hostamar with systemd journal support
# Env: HEALTH_URL (default: https://hostamar.com/api/health)
#      LOG_FILE (optional: if set, logs to file; otherwise uses stdout for systemd journal)

HEALTH_URL="${HEALTH_URL:-https://hostamar.com/api/health}"
LOG_FILE="${LOG_FILE:-}"

if [[ -n "$LOG_FILE" ]]; then
  mkdir -p "$(dirname "$LOG_FILE")"
fi

TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Capture body and trailing line with code/time in a single call
OUT="$(curl -sS --max-time 10 -w '\n%{http_code} %{time_total}\n' "$HEALTH_URL" || true)"
CODE_TIME_LINE="$(printf "%s" "$OUT" | tail -n 1)"
BODY="$(printf "%s" "$OUT" | sed '$d')"
HTTP_CODE="$(awk '{print $1}' <<<"$CODE_TIME_LINE")"
TOTAL_TIME="$(awk '{print $2}' <<<"$CODE_TIME_LINE")"

log_msg() {
  local msg="$1"
  if [[ -n "$LOG_FILE" ]]; then
    echo "$msg" >> "$LOG_FILE"
  else
    echo "$msg"
  fi
}

if [[ "${HTTP_CODE}" != "200" ]]; then
  log_msg "$TS | UPTIME | FAIL | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL}"
  exit 1
fi

if ! grep -qi '"status"\s*:\s*"ok"' <<<"$BODY"; then
  log_msg "$TS | UPTIME | WARN | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL} body_missing_status_ok"
  exit 0
fi

log_msg "$TS | UPTIME | OK | code=${HTTP_CODE} time=${TOTAL_TIME} url=${HEALTH_URL}"
