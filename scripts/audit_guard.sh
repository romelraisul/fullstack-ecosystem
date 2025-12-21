#!/bin/bash

# ==========================================
# Hostamar Audit Guard
# "The Silent Observer"
# ==========================================

LOG_DIR="/var/log/hostamar/audit"
WATCH_DIR="/opt/hostamar"
DATE=$(date "+%Y-%m-%d")
FILE_LOG="$LOG_DIR/files_$DATE.log"
PROCESS_LOG="$LOG_DIR/process_$DATE.log"
NET_LOG="$LOG_DIR/network_$DATE.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "[$(date)] Starting Audit Guard..." >> "$PROCESS_LOG"

# 1. File System Monitoring (Real-time)
# Requires: apt-get install inotify-tools
if command -v inotifywait >/dev/null; then
    echo "[INFO] Starting File Watcher on $WATCH_DIR" >> "$FILE_LOG"
    # Run in background
    inotifywait -m -r -e create,delete,modify,move --format '%w%f %e %T' --timefmt '%H:%M:%S' "$WATCH_DIR" >> "$FILE_LOG" &
    FILE_PID=$!
else
    echo "[WARN] inotify-tools not found. Installing..." >> "$FILE_LOG"
    apt-get update && apt-get install -y inotify-tools
    inotifywait -m -r -e create,delete,modify,move --format '%w%f %e %T' --timefmt '%H:%M:%S' "$WATCH_DIR" >> "$FILE_LOG" &
    FILE_PID=$!
fi

# 2. Process & Network Monitoring Loop (Periodic)
while true; do
    TIMESTAMP=$(date "+%H:%M:%S")
    
    # Process Snapshot (Top 5 CPU consumers)
    echo "--- $TIMESTAMP ---" >> "$PROCESS_LOG"
    ps -eo pid,user,%cpu,%mem,cmd --sort=-%cpu | head -n 6 >> "$PROCESS_LOG"
    
    # Network Snapshot (Established Connections)
    echo "--- $TIMESTAMP ---" >> "$NET_LOG"
    ss -tun state established >> "$NET_LOG"
    
    # Check for Anomalies (Simple Logic: CPU > 80%)
    HIGH_CPU=$(ps -eo %cpu --sort=-%cpu | head -n 2 | tail -n 1 | cut -d. -f1)
    if [ "$HIGH_CPU" -gt 80 ]; then
        echo "[ALERT] High CPU detected at $TIMESTAMP" >> "$PROCESS_LOG"
    fi

    sleep 60
done
