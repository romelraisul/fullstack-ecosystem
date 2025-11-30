# Hostamar Monitoring & Maintenance

This folder contains simple, production-friendly monitoring helpers:
- Uptime checker hitting the health endpoint
- TLS expiry checker for your domain
- Cron installer to schedule the checks
- Logrotate samples for Nginx and PM2 logs

## Files
- `uptime_check.sh`: Checks `HEALTH_URL` (default: https://hostamar.com/api/health) every run.
- `tls_expiry_check.sh`: Checks certificate days remaining for `DOMAIN` (default: hostamar.com).
- `install_cron.sh`: Installs the scripts into `/usr/local/bin`, sets cron, and installs logrotate configs.
- `logrotate/hostamar-nginx.conf`: Rotates `/var/log/nginx/hostamar*.log` weekly.
- `logrotate/hostamar-pm2.conf`: Rotates PM2 logs weekly with copytruncate.

## Quick Setup (run on the VM)
```bash
cd ~/hostamar-platform/deploy/monitoring
chmod +x uptime_check.sh tls_expiry_check.sh install_cron.sh
sudo ./install_cron.sh \
  --domain hostamar.com \
  --health-url https://hostamar.com/api/health \
  --pm2-user "$USER" \
  --pm2-logs "/home/$USER/.pm2/logs/*.log"

# Verify cron and initial runs
sudo systemctl status cron | cat
sudo bash -c '/usr/local/bin/hostamar-uptime-check.sh && /usr/local/bin/hostamar-tls-expiry-check.sh' || true
sudo tail -n 100 /var/log/hostamar/cron.log
```

## Notes
- Cron schedule defaults: uptime every 5 minutes, TLS check daily at 03:00.
- Edit `/etc/cron.d/hostamar-monitoring` to customize schedule.
- For PM2 autostart after reboot, see `deploy/pm2_setup.sh`.