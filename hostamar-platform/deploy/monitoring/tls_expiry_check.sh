#!/usr/bin/env bash
set -euo pipefail

# TLS expiry checker for Hostamar
# Env: DOMAIN (default: hostamar.com)
#      LOG_FILE (default: /var/log/hostamar/tls_expiry_check.log)
# Exit non-zero only on unexpected errors; warn when below threshold.

DOMAIN="${DOMAIN:-hostamar.com}"
LOG_FILE="${LOG_FILE:-/var/log/hostamar/tls_expiry_check.log}"
THRESHOLD_DAYS="${THRESHOLD_DAYS:-14}"

mkdir -p "$(dirname "$LOG_FILE")"
TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

set +e
END_DATE_RAW=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -enddate)
RET=$?
set -e

if [[ $RET -ne 0 || -z "$END_DATE_RAW" ]]; then
  echo "$TS | TLS | ERROR | domain=${DOMAIN} msg=failed_to_fetch_certificate" >> "$LOG_FILE"
  exit 0
fi

# END_DATE_RAW like: notAfter=Feb 27 17:15:26 2026 GMT
END_DATE_STR=${END_DATE_RAW#notAfter=}
END_EPOCH=$(date -u -d "$END_DATE_STR" +%s)
NOW_EPOCH=$(date -u +%s)
REMAIN_DAYS=$(( (END_EPOCH - NOW_EPOCH) / 86400 ))

if (( REMAIN_DAYS < THRESHOLD_DAYS )); then
  echo "$TS | TLS | WARN | domain=${DOMAIN} days_left=${REMAIN_DAYS} threshold=${THRESHOLD_DAYS}" >> "$LOG_FILE"
else
  echo "$TS | TLS | OK | domain=${DOMAIN} days_left=${REMAIN_DAYS}" >> "$LOG_FILE"
fi