#!/usr/bin/env bash
set -euo pipefail

# TLS expiry checker for Hostamar with systemd journal support
# Env: CERT_DOMAIN (default: hostamar.com)
#      WARN_DAYS (default: 30)
#      LOG_FILE (optional: if set, logs to file; otherwise uses stdout for systemd journal)

CERT_DOMAIN="${CERT_DOMAIN:-hostamar.com}"
WARN_DAYS="${WARN_DAYS:-30}"
LOG_FILE="${LOG_FILE:-}"

if [[ -n "$LOG_FILE" ]]; then
  mkdir -p "$(dirname "$LOG_FILE")"
fi

TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Get certificate expiry date
EXPIRY_DATE="$(echo | openssl s_client -servername "$CERT_DOMAIN" -connect "$CERT_DOMAIN:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)"

if [[ -z "$EXPIRY_DATE" ]]; then
  if [[ -n "$LOG_FILE" ]]; then
    echo "$TS | TLS | FAIL | domain=${CERT_DOMAIN} unable_to_retrieve_cert" >> "$LOG_FILE"
  else
    echo "$TS | TLS | FAIL | domain=${CERT_DOMAIN} unable_to_retrieve_cert"
  fi
  exit 1
fi

EXPIRY_EPOCH="$(date -d "$EXPIRY_DATE" +%s)"
NOW_EPOCH="$(date +%s)"
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

log_msg() {
  local msg="$1"
  if [[ -n "$LOG_FILE" ]]; then
    echo "$msg" >> "$LOG_FILE"
  else
    echo "$msg"
  fi
}

if [[ "$DAYS_LEFT" -lt "$WARN_DAYS" ]]; then
  log_msg "$TS | TLS | WARN | domain=${CERT_DOMAIN} days_left=${DAYS_LEFT} threshold=${WARN_DAYS}"
  exit 0
fi

log_msg "$TS | TLS | OK | domain=${CERT_DOMAIN} days_left=${DAYS_LEFT}"
