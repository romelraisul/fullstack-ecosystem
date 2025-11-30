# Monitoring with Systemd Timers

This directory contains systemd service and timer units for monitoring the Hostamar platform.

## Features

- **Better logging**: Output captured in systemd journal with structured metadata
- **Service management**: Start, stop, restart timers with `systemctl`
- **Persistent scheduling**: Timers survive reboots and catch up on missed runs
- **Flexible configuration**: Override environment variables via service units

## Files

- `hostamar-uptime-check.service` / `hostamar-uptime-check.timer` – Health endpoint check (every 5 minutes)
- `hostamar-tls-expiry-check.service` / `hostamar-tls-expiry-check.timer` – TLS certificate expiry check (daily at 03:00 UTC)
- `install_systemd_timers.sh` – Installer script
- `hostamar-uptime-check.sh` – Uptime check script (systemd-aware version)
- `hostamar-tls-expiry-check.sh` – TLS expiry check script (systemd-aware version)

## Installation

```bash
# Local install (on repo host) then copy to server if using scp
cd deploy/monitoring/systemd
chmod +x install_systemd_timers.sh hostamar-uptime-check.sh hostamar-tls-expiry-check.sh
./install_systemd_timers.sh
```

```bash
# Remote install via temporary public GCS objects (no scp needed)
# 1. Upload files to bucket (example: hostamar-deploy)
# 2. Grant objectViewer to allUsers temporarily
# 3. On VM:
cd /tmp
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/install_systemd_timers.sh
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-uptime-check.sh
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-tls-expiry-check.sh
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-uptime-check.service
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-uptime-check.timer
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-tls-expiry-check.service
curl -fLO https://storage.googleapis.com/hostamar-deploy/systemd/hostamar-tls-expiry-check.timer
sudo install -m 0755 hostamar-uptime-check.sh /usr/local/bin/
sudo install -m 0755 hostamar-tls-expiry-check.sh /usr/local/bin/
sudo install -m 0644 hostamar-uptime-check.service /etc/systemd/system/
sudo install -m 0644 hostamar-uptime-check.timer /etc/systemd/system/
sudo install -m 0644 hostamar-tls-expiry-check.service /etc/systemd/system/
sudo install -m 0644 hostamar-tls-expiry-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hostamar-uptime-check.timer hostamar-tls-expiry-check.timer
# 4. Remove public access from bucket afterwards
```

## Usage

### Check timer status

```bash
systemctl list-timers --all | grep hostamar
sudo systemctl status hostamar-uptime-check.timer
sudo systemctl status hostamar-tls-expiry-check.timer
```

### View logs

```bash
# Follow uptime check logs
sudo journalctl -u hostamar-uptime-check.service -f

# Follow TLS expiry logs
sudo journalctl -u hostamar-tls-expiry-check.service -f

# View recent logs
sudo journalctl -u hostamar-uptime-check.service --since "1 hour ago"
sudo journalctl -u hostamar-tls-expiry-check.service --since "1 day ago"
```

### Manually trigger checks

```bash
sudo systemctl start hostamar-uptime-check.service
sudo systemctl start hostamar-tls-expiry-check.service
```

### Stop/disable timers

```bash
sudo systemctl stop hostamar-uptime-check.timer
sudo systemctl disable hostamar-uptime-check.timer

sudo systemctl stop hostamar-tls-expiry-check.timer
sudo systemctl disable hostamar-tls-expiry-check.timer
```

## Environment Variables

Override in service units using `Environment=` or `EnvironmentFile=`:

### Uptime Check

- `HEALTH_URL` – Health endpoint URL (default: `https://hostamar.com/api/health`)
- `LOG_FILE` – Optional file path (if unset, logs to journal only)
- `CURL_OPTS` – Extra curl flags (e.g. `--max-time 10 --connect-timeout 5`)

### TLS Expiry Check

- `CERT_DOMAIN` – Domain to check (default: `hostamar.com`)
- `WARN_DAYS` – Warning threshold in days (default: `30`)
- `LOG_FILE` – Optional file path (if unset, logs to journal only)
- `TLS_HOST` / `TLS_PORT` – Override target host & port if script supports env host instead of CERT_DOMAIN.

Example override (edit service file):

```ini
[Service]
Environment="HEALTH_URL=https://hostamar.com/api/health"
Environment="WARN_DAYS=14"
Environment="CURL_OPTS=--max-time 10 --connect-timeout 5"
```

### Drop-in override (preferred)

Instead of editing the unit file directly:

```bash
sudo systemctl edit hostamar-uptime-check.service
# Add under [Service]:
# Environment="HEALTH_URL=https://example.com/health" "CURL_OPTS=--max-time 5"
sudo systemctl daemon-reload
sudo systemctl restart hostamar-uptime-check.timer
```

## Verification

After install:

```bash
sudo systemctl list-timers --all | grep hostamar
sudo systemctl start hostamar-uptime-check.service
sudo systemctl start hostamar-tls-expiry-check.service
journalctl -u hostamar-uptime-check.service -n 20 --no-pager
journalctl -u hostamar-tls-expiry-check.service -n 20 --no-pager
```

Expected log patterns:

- Uptime: `hostamar-uptime-check OK` or warning/fail lines
- TLS Expiry: `TLS expiry OK` / `WARNING` when below threshold

## Maintenance Script

Consider adding a helper script (e.g. `gateway-monitoring-maintenance.sh`) to:

1. Run both services immediately
2. Tail last 20 log lines
3. Show timer next-run times
4. Validate environment overrides
5. (Optional) Reapply iptables MASQUERADE NAT dedupe if networking layer changes

## Security Notes

- Remove public bucket IAM after remote install
- Prefer signed URLs via service account for production automation
- Use `journalctl --unit` filtered queries instead of saving logs to world-readable files

## Advantages over Cron

- Centralized logging via `journalctl` with structured metadata
- Better error handling and service state management
- Persistent timers catch up on missed runs after system downtime
- Easier to query logs by service unit
- No need for separate logrotate configs (journald manages rotation)

## Coexistence with Cron

You can run both cron jobs and systemd timers if desired. If switching from cron to systemd:

1. Disable cron entries: `sudo rm /etc/cron.d/hostamar-monitoring`
2. Install systemd timers: `./install_systemd_timers.sh`
3. Verify timers are active: `systemctl list-timers --all | grep hostamar`
