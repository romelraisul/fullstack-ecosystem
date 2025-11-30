# 🚀 Hostamar Platform - Deployment Guide

## Complete Automated Deployment (Recommended)

### One-Command Full Deployment

```powershell
# Deploy everything (Python venv + VM setup + App + Nginx + SSL)
.\deploy-hostamar-full.ps1 -Domain "hostamar.com"

# Skip certain steps if already done
.\deploy-hostamar-full.ps1 -SkipVenvSetup -SkipVMPrep -Domain "hostamar.com"

# Deploy without SSL (for testing)
.\deploy-hostamar-full.ps1 -SkipSSL
```

**Duration:** 15-20 minutes for complete deployment

---

## Manual Step-by-Step Deployment

### Prerequisites
- SSH access to GCP VM (`hostamar-iap` configured in `~/.ssh/config`)
- Domain DNS pointing to VM IP (for SSL)
- Windows PowerShell / WSL with rsync

---

### Step 1: Setup Python Virtual Environment (Local)

```powershell
.\scripts\setup-python-venv.ps1
```

**What it does:**
- Creates `aiauto_venv` with all AI agent dependencies
- Installs Microsoft Agent Framework (with `--pre` flag)
- Prepares environment for evaluation framework

---

### Step 2: Prepare GCP VM

```bash
# SSH to VM
ssh hostamar-iap

# Run preparation script
bash /tmp/vm-prepare.sh
```

Or upload and run remotely:
```powershell
scp .\hostamar-platform\deploy\vm-prepare.sh hostamar-iap:/tmp/
ssh hostamar-iap "chmod +x /tmp/vm-prepare.sh && /tmp/vm-prepare.sh"
```

**What it installs:**
- Node.js 20 LTS
- PM2 process manager
- PostgreSQL database
- Nginx web server
- Certbot (Let's Encrypt)

---

### Step 3: Deploy Application

```powershell
.\hostamar-platform\deploy\deploy-to-gcp.ps1 -SSHHost hostamar-iap
```

**What it does:**
1. Builds Next.js app locally
2. Creates `.env.production` with secure secrets
3. Syncs files via rsync (excludes node_modules, .git)
4. Installs dependencies on VM
5. Runs Prisma migrations
6. Builds on VM
7. Starts app with PM2
8. Verifies health endpoint

**App runs on:** `http://localhost:3001`

---

### Step 4: Configure Nginx

```bash
# SSH to VM
ssh hostamar-iap

# Upload and run Nginx config script
bash /tmp/nginx-config.sh hostamar.com
```

Or from local:
```powershell
scp .\hostamar-platform\deploy\nginx-config.sh hostamar-iap:/tmp/
ssh hostamar-iap "chmod +x /tmp/nginx-config.sh && /tmp/nginx-config.sh hostamar.com"
```

**What it does:**
- Creates Nginx reverse proxy config
- Routes http://hostamar.com → http://localhost:3001
- Adds security headers
- Enables caching for static files

---

### Step 5: Setup SSL Certificate

**⚠️ Before running:**
1. Ensure DNS `hostamar.com` → VM public IP
2. Open firewall ports 80/443
3. Verify: `curl http://YOUR_VM_IP` (should reach Nginx)

```bash
# SSH to VM
ssh hostamar-iap

# Run SSL setup
bash /tmp/setup-ssl.sh hostamar.com romelraisul@gmail.com
```

Or from local:
```powershell
scp .\hostamar-platform\deploy\setup-ssl.sh hostamar-iap:/tmp/
ssh hostamar-iap "chmod +x /tmp/setup-ssl.sh && /tmp/setup-ssl.sh hostamar.com romelraisul@gmail.com"
```

**What it does:**
- Obtains Let's Encrypt SSL certificate
- Configures Nginx for HTTPS
- Sets up auto-renewal (certbot.timer)

---

## Verification

### Check Application Status
```bash
ssh hostamar-iap

# PM2 status
pm2 status

# View logs
pm2 logs hostamar-platform

# Real-time monitoring
pm2 monit
```

### Test Endpoints
```bash
# Health check
curl http://localhost:3001/api/health

# From outside (if SSL setup)
curl https://hostamar.com/api/health
```

### Check Database
```bash
ssh hostamar-iap

# Connect to PostgreSQL
sudo -u postgres psql -d hostamar

# List tables
\dt

# Exit
\q
```

### Verify Monitoring Timers
```bash
ssh hostamar-iap

# List scheduled timers
systemctl list-timers hostamar-*

# Check uptime logs
journalctl -u hostamar-uptime-check.service -n 20

# Check TLS expiry logs
journalctl -u hostamar-tls-expiry-check.service -n 20
```

---

## Troubleshooting

### Application not starting
```bash
# Check PM2 logs
pm2 logs hostamar-platform --lines 50

# Check Node.js version
node --version  # Should be 20.x

# Restart app
pm2 restart hostamar-platform
```

### Database connection errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database exists
sudo -u postgres psql -l | grep hostamar

# Test connection
psql "postgresql://hostamar_user:hostamar_secure_2025@localhost:5432/hostamar"
```

### Nginx errors
```bash
# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/hostamar-error.log

# Reload Nginx
sudo systemctl reload nginx
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --nginx

# View certbot logs
sudo journalctl -u certbot.service -n 50
```

---

## Maintenance Commands

### Update Application
```powershell
# From local machine
.\hostamar-platform\deploy\deploy-to-gcp.ps1 -SkipBackup
```

### Database Backup
```bash
ssh hostamar-iap
sudo -u postgres pg_dump hostamar > ~/hostamar-backup-$(date +%Y%m%d).sql
```

### View All Logs
```bash
ssh hostamar-iap

# PM2 logs
pm2 logs

# Nginx access logs
sudo tail -f /var/log/nginx/hostamar-access.log

# System logs
sudo journalctl -f
```

### Stop/Start Application
```bash
ssh hostamar-iap

# Stop
pm2 stop hostamar-platform

# Start
pm2 start hostamar-platform

# Restart
pm2 restart hostamar-platform

# Delete from PM2
pm2 delete hostamar-platform
```

---

## Files Created

### Local Scripts
- `scripts/setup-python-venv.ps1` - Python venv setup
- `deploy-hostamar-full.ps1` - Master orchestrator
- `hostamar-platform/deploy/deploy-to-gcp.ps1` - App deployment
- `hostamar-platform/deploy/vm-prepare.sh` - VM preparation
- `hostamar-platform/deploy/nginx-config.sh` - Nginx setup
- `hostamar-platform/deploy/setup-ssl.sh` - SSL certificate

### On GCP VM
- `/var/www/hostamar/` - Application directory
- `/etc/nginx/sites-available/hostamar` - Nginx config
- `~/hostamar-backup-*.tar.gz` - Backups
- `~/.pm2/` - PM2 configuration

---

## Architecture

```
Internet
    ↓
[Nginx :80/443] (hostamar.com)
    ↓
[Next.js :3001] (PM2 managed)
    ↓
[PostgreSQL :5432]

Monitoring:
- Systemd timers (uptime + TLS checks)
- PM2 process monitoring
- Nginx access/error logs
- journalctl for system logs
```

---

## What Gets Deployed

| Component | Technology | Port | Status |
|-----------|-----------|------|--------|
| Web App | Next.js 14 | 3001 | PM2 managed |
| Database | PostgreSQL | 5432 | systemd |
| Reverse Proxy | Nginx | 80/443 | systemd |
| SSL | Let's Encrypt | - | Auto-renewal |
| Monitoring | Systemd Timers | - | Active |
| Process Manager | PM2 | - | Active |

---

## Next Steps After Deployment

1. **Test Authentication**
   - Visit: `https://hostamar.com/auth/signup`
   - Create test account
   - Login and verify dashboard

2. **Setup Payment Gateway**
   - Integrate bKash/Nagad/Stripe
   - Update Prisma schema for transactions

3. **Video Generation Pipeline**
   - Implement AI video script generator
   - Setup video rendering service
   - Configure storage (S3/MinIO)

4. **Enable CI/CD**
   - Configure GitHub Actions
   - Auto-deploy on push to main

5. **Marketing**
   - Share signup link
   - Create demo videos
   - Launch social media campaign

---

## Support

### Quick Help
```bash
# SSH to VM
ssh hostamar-iap

# Check everything
pm2 status && \
sudo systemctl status nginx && \
sudo systemctl status postgresql && \
systemctl list-timers hostamar-*
```

### Contact
- Email: romelraisul@gmail.com
- GitHub: Check repo issues

---

**🎉 Happy Deploying!**
