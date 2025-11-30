#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

echo "[INFO] Installing systemd monitoring timers for hostamar..."

# Ensure scripts are installed
if [[ ! -f /usr/local/bin/hostamar-uptime-check.sh ]]; then
    echo "[ERROR] /usr/local/bin/hostamar-uptime-check.sh not found. Run install_cron.sh first."
    exit 1
fi

if [[ ! -f /usr/local/bin/hostamar-tls-expiry-check.sh ]]; then
    echo "[ERROR] /usr/local/bin/hostamar-tls-expiry-check.sh not found. Run install_cron.sh first."
    exit 1
fi

# Install uptime check service and timer
echo "[INFO] Installing uptime check service and timer..."
sudo cp "${SCRIPT_DIR}/hostamar-uptime-check.service" "${SYSTEMD_DIR}/"
sudo cp "${SCRIPT_DIR}/hostamar-uptime-check.timer" "${SYSTEMD_DIR}/"

# Install TLS expiry check service and timer
echo "[INFO] Installing TLS expiry check service and timer..."
sudo cp "${SCRIPT_DIR}/hostamar-tls-expiry-check.service" "${SYSTEMD_DIR}/"
sudo cp "${SCRIPT_DIR}/hostamar-tls-expiry-check.timer" "${SYSTEMD_DIR}/"

# Reload systemd
echo "[INFO] Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start timers
echo "[INFO] Enabling and starting timers..."
sudo systemctl enable hostamar-uptime-check.timer
sudo systemctl start hostamar-uptime-check.timer

sudo systemctl enable hostamar-tls-expiry-check.timer
sudo systemctl start hostamar-tls-expiry-check.timer

echo ""
echo "[DONE] Systemd timers installed and started."
echo ""
echo "Verify status:"
echo "  sudo systemctl status hostamar-uptime-check.timer"
echo "  sudo systemctl status hostamar-tls-expiry-check.timer"
echo ""
echo "View logs:"
echo "  sudo journalctl -u hostamar-uptime-check.service -f"
echo "  sudo journalctl -u hostamar-tls-expiry-check.service -f"
echo ""
echo "List all timer units:"
echo "  systemctl list-timers --all | grep hostamar"
