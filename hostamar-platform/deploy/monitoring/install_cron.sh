#!/usr/bin/env bash
set -euo pipefail

# Install monitoring cron jobs and logrotate configs
# Usage:
#   sudo ./install_cron.sh \
#     --domain hostamar.com \
#     --health-url https://hostamar.com/api/health \
#     --pm2-user romel \
#     --pm2-logs /home/romel/.pm2/logs/*.log

DOMAIN="hostamar.com"
HEALTH_URL="https://hostamar.com/api/health"
PM2_USER="${SUDO_USER:-${USER}}"
PM2_LOGS="/home/${PM2_USER}/.pm2/logs/*.log"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2;;
    --health-url) HEALTH_URL="$2"; shift 2;;
    --pm2-user) PM2_USER="$2"; PM2_LOGS="/home/${PM2_USER}/.pm2/logs/*.log"; shift 2;;
    --pm2-logs) PM2_LOGS="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "[INFO] Installing binaries into /usr/local/bin..."
install -m 0755 uptime_check.sh /usr/local/bin/hostamar-uptime-check.sh
install -m 0755 tls_expiry_check.sh /usr/local/bin/hostamar-tls-expiry-check.sh

echo "[INFO] Ensuring log directory..."
mkdir -p /var/log/hostamar

CRON_FILE="/etc/cron.d/hostamar-monitoring"
echo "[INFO] Writing cron file: ${CRON_FILE}"
cat > "$CRON_FILE" <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Environment for scripts
HEALTH_URL=${HEALTH_URL}
DOMAIN=${DOMAIN}
LOG_FILE=/var/log/hostamar/cron_task.log

# Every 5 minutes: uptime check
*/5 * * * * root /usr/local/bin/hostamar-uptime-check.sh >> /var/log/hostamar/cron_task.log 2>&1

# Daily at 03:00: TLS expiry check
0 3 * * * root /usr/local/bin/hostamar-tls-expiry-check.sh >> /var/log/hostamar/cron_task.log 2>&1
EOF

chmod 0644 "$CRON_FILE"

echo "[INFO] Installing logrotate configs..."
install -m 0644 logrotate/hostamar-nginx.conf /etc/logrotate.d/hostamar-nginx

# PM2 logs rotation (user-owned)
sed "s|__PM2_LOGS__|${PM2_LOGS}|g; s|__PM2_USER__|${PM2_USER}|g" \
  logrotate/hostamar-pm2.conf > /etc/logrotate.d/hostamar-pm2
chmod 0644 /etc/logrotate.d/hostamar-pm2

echo "[INFO] Reloading cron..."
systemctl restart cron || service cron restart || true

echo "[DONE] Monitoring installed. Verify with: tail -n 100 /var/log/hostamar/cron_task.log"