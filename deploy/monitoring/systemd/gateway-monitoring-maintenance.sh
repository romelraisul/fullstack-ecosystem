#!/usr/bin/env bash
set -euo pipefail

# gateway-monitoring-maintenance.sh
# Utility script to inspect and operate Hostamar monitoring timers & networking state.

SCRIPT_NAME="gateway-monitoring-maintenance.sh"
LOG_LINES_DEFAULT=20
SUBNET="10.10.0.0/24"

usage() {
  cat <<EOF
$SCRIPT_NAME - maintenance helper

Usage: $SCRIPT_NAME [command] [options]

Commands:
  status            Show systemd status summary for services & timers
  run               Manually run both monitoring services now
  logs              Show last N lines (default: $LOG_LINES_DEFAULT) of both service logs
  timers            List next and last run times for monitoring timers
  env               Display effective environment overrides for services
  dedupe-nat        Ensure single MASQUERADE rule for $SUBNET on current egress iface
  verify            Composite: status + timers + logs (last $LOG_LINES_DEFAULT)
  help              Show this help

Options:
  -n <lines>        Override number of log lines for 'logs' or 'verify'

Examples:
  $SCRIPT_NAME status
  $SCRIPT_NAME logs -n 50
  $SCRIPT_NAME dedupe-nat
EOF
}

# Determine egress interface
get_iface() {
  local iface
  iface=$(ip -o -4 route show default | awk '{print $5}') || true
  echo "${iface:-ens4}" # fallback
}

service_names=(hostamar-uptime-check hostamar-tls-expiry-check)
timer_names=(hostamar-uptime-check hostamar-tls-expiry-check)

status() {
  echo "== Systemd Service Status =="
  for s in "${service_names[@]}"; do
    systemctl is-active "$s.service" 2>/dev/null || true
    systemctl status "$s.service" --no-pager -n 0 | awk '/Loaded:|Active:/'
    echo
  done
  echo "== Systemd Timer Status =="
  for t in "${timer_names[@]}"; do
    systemctl status "$t.timer" --no-pager -n 0 | awk '/Loaded:|Active:/'
    echo
  done
}

run_services() {
  echo "== Running monitoring services =="
  for s in "${service_names[@]}"; do
    echo "Running: $s.service";
    systemctl start "$s.service" || true
  done
}

show_logs() {
  local lines=${1:-$LOG_LINES_DEFAULT}
  echo "== Last $lines lines: hostamar-uptime-check.service =="
  journalctl -u hostamar-uptime-check.service -n "$lines" --no-pager || true
  echo
  echo "== Last $lines lines: hostamar-tls-expiry-check.service =="
  journalctl -u hostamar-tls-expiry-check.service -n "$lines" --no-pager || true
}

show_timers() {
  echo "== Timer List (filtered) =="
  systemctl list-timers --all | grep -E 'hostamar-(uptime|tls-expiry)-check' || true
}

env_effective() {
  echo "== Effective Environment Overrides =="
  for s in "${service_names[@]}"; do
    echo "-- $s.service --"
    systemctl show "$s.service" -p Environment | sed 's/^Environment=//' || true
    echo
  done
}

dedupe_nat() {
  local iface; iface=$(get_iface)
  echo "Using egress iface: $iface"
  echo "Current MASQUERADE rules:";
  sudo iptables -t nat -S POSTROUTING | grep MASQUERADE || true

  # Remove duplicates for subnet+iface
  while sudo iptables -t nat -C POSTROUTING -s "$SUBNET" -o "$iface" -j MASQUERADE 2>/dev/null; do
    sudo iptables -t nat -D POSTROUTING -s "$SUBNET" -o "$iface" -j MASQUERADE || true
  done
  # Remove broad iface-only MASQUERADE
  sudo iptables -t nat -D POSTROUTING -o "$iface" -j MASQUERADE 2>/dev/null || true
  # Re-add single canonical rule
  sudo iptables -t nat -A POSTROUTING -s "$SUBNET" -o "$iface" -j MASQUERADE
  sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null
  echo "Post-dedupe MASQUERADE rules:";
  sudo iptables -t nat -S POSTROUTING | grep MASQUERADE || true
}

verify() {
  status
  show_timers
  show_logs "$1"
}

main() {
  local cmd=${1:-help}; shift || true
  local lines=$LOG_LINES_DEFAULT
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -n) lines="$2"; shift 2;;
      *) break;;
    esac
  done
  case "$cmd" in
    status)       status;;
    run)          run_services;;
    logs)         show_logs "$lines";;
    timers)       show_timers;;
    env)          env_effective;;
    dedupe-nat)   dedupe_nat;;
    verify)       verify "$lines";;
    help|*)       usage;;
  esac
}

main "$@"
