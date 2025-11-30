# 🚀 Hostamar Platform Deployment Checklist

আপনার রিপোর্ট অনুযায়ী সম্পূর্ণ deployment verify করার জন্য এই checklist follow করুন।

## 📋 Pre-Deployment Checklist
### Local Machine Setup
- [ ] **gcloud CLI installed**
  ```bash
  gcloud --version
  ```

- [ ] **Authenticated with GCP**
  ```bash
  # Should show active account
  ```

- [ ] **Project configured**
### Application Health
- [ ] **Port 3001 listening**
  ```bash
  ssh REMOTE_HOST "ss -tlnp | grep :3001 || sudo netstat -tlnp | grep :3001"
  # Should show next-server listening on 0.0.0.0:3001
  ```

- [ ] **Health endpoint responds (direct)**
  ```bash
  ssh REMOTE_HOST "curl -s http://127.0.0.1:3001/api/health | jq '.status'"
  # Expected: "ok"
  ```

- [ ] **Homepage loads (direct)**
  ```bash
  ssh REMOTE_HOST "curl -s http://127.0.0.1:3001 | grep -i hostamar"
  # Should return HTML with "hostamar"
  ```
  ```bash
  gcloud config get-value project
  ```

- [ ] **VS Code installed** with extensions:
### Nginx Configuration
- [ ] **Config file exists**
  ```bash
  ssh REMOTE_HOST "sudo head -20 /etc/nginx/sites-available/hostamar"
  ```
  - [ ] Remote - SSH

- [ ] **Git repository**
  - [ ] All changes committed
  - [ ] `.gitignore` excludes sensitive files
 - [ ] **Reverse proxy working**
  ```bash
  curl -H "Host: hostamar.com" -s http://VM_EXTERNAL_IP | grep -i hostamar
  # Should return HTML (port 80 works via Host header)
  ```
  - [ ] No `.env` files in Git

  gcloud compute instances describe mumbai-instance-1 --zone=asia-south1-a
  ```

- [ ] **External IP available**
  ```bash
      --zone=asia-south1-a \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
  ```

  ```bash
### DNS Configuration
- [ ] **Registrar or Cloud DNS configured**
  - Option A (Registrar DNS e.g., Namecheap):
    - Add `A` record `@` → `VM_EXTERNAL_IP`, TTL Auto
    - Add `A` record `www` → `VM_EXTERNAL_IP`, TTL Auto
  - Option B (Cloudflare):
    - Add site to Cloudflare; switch nameservers at registrar
    - Add `A` record `@` and `www` → `VM_EXTERNAL_IP`
    - For initial Certbot HTTP validation, set Proxy: OFF (DNS only), then re-enable proxy
    - SSL/TLS Mode: **Full (strict)** after cert issuance
  gcloud compute config-ssh
  ssh mumbai-instance-1.asia-south1-a.YOUR_PROJECT_ID "echo Connection OK"

- [ ] **Firewall rules configured**
  ```bash
  ```
  Should have:
  - [ ] Port 22 (SSH) open
  - [ ] Port 80 (HTTP) open
  - [ ] Port 443 (HTTPS) open

### Domain & DNS (Optional for initial testing)
- [ ] **Cloudflare account** setup
- [ ] **DNS records prepared** (don't add yet, after deployment)

---
## 🔧 Deployment Phase 1: Code Upload

### Script Configuration
- [ ] **Edit `deploy/gcp-mumbai-deploy.sh`**
### SSL Certificate
- [ ] **Certbot installed**
  ```bash
  ssh REMOTE_HOST "certbot --version"
  ```

- [ ] **Issue certificate (after DNS resolves)**
  ```bash
  ssh REMOTE_HOST "sudo certbot --nginx -d hostamar.com -d www.hostamar.com --agree-tos -m admin@hostamar.com --redirect"
  ```

- [ ] **Certificate present**
  ```bash
  ssh REMOTE_HOST "sudo certbot certificates | sed -n '1,120p'"
  # Should list hostamar.com with both domains and a valid expiry date
  ```

- [ ] **HTTPS redirect working**
  ```bash
  curl -I http://hostamar.com
  # Expected: 301 Moved Permanently → https://hostamar.com
  ```

- [ ] **HTTPS responding**
  ```bash
  curl -I https://hostamar.com
  # Expected: 200 OK
  ```
  ```bash
  VM_NAME="mumbai-instance-1"        # ✓ Your VM name
  ZONE="asia-south1-a"               # ✓ Mumbai zone
  PROJECT_ID="your-project-id"       # ⚠️ UPDATE THIS
  REMOTE_USER="romelraisul"          # ✓ Your username
  ```

### Run Deployment
- [ ] **Execute deployment script**
  ```bash
  cd c:/Users/romel/OneDrive/Documents/aiauto/hostamar-platform
  bash deploy/gcp-mumbai-deploy.sh
  ```

### Verify Upload
- [ ] **Check files on VM**
  ```bash
  ssh REMOTE_HOST "ls -lh ~/hostamar-platform"
  ```
  Should see:
  - [ ] `package.json`
  - [ ] `app/` directory
  - [ ] `prisma/` directory
  - [ ] NO `node_modules/` (will be installed on VM)

- [ ] **Verify .env created**
  ```bash
  ssh REMOTE_HOST "cat ~/hostamar-platform/.env | head -3"
  ```
  Should show:
  ```
  DATABASE_URL="file:./prod.db"
  NEXTAUTH_URL="https://hostamar.com"
  ...
  ```

---

## 🛠️ Deployment Phase 2: Environment Setup

### Node.js & Dependencies
- [ ] **Node.js installed**
  ```bash
  ssh REMOTE_HOST "node --version"
  # Expected: v20.x.x
  ```

- [ ] **npm install completed**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && ls node_modules | wc -l"
  # Expected: 400+ packages
  ```

### Database Setup
- [ ] **Prisma Client generated**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && ls node_modules/@prisma/client"
  ```

- [ ] **Database pushed**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && ls -lh prod.db"
  # Should exist with ~100KB+ size
  ```

- [ ] **Tables created**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma db pull"
  # Should show Customer, Business, Video, Subscription tables
  ```

### Production Build
- [ ] **Next.js build successful**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && ls .next/BUILD_ID"
  # Should exist
  ```

- [ ] **Build logs clean**
  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform && grep -i error .next/trace 2>/dev/null"
  # Should be empty or file not found (no errors)
  ```

---

## 🚦 Deployment Phase 3: Process Management

### PM2 Setup
- [ ] **PM2 installed**
  ```bash
  ssh REMOTE_HOST "pm2 --version"
  # Expected: 5.x.x
  ```

- [ ] **App running**
  ```bash
  ssh REMOTE_HOST "pm2 status"
  ```
  Should show:
  ```
  │ hostamar │ online │
  ```

- [ ] **Process details**
  ```bash
  ssh REMOTE_HOST "pm2 info hostamar"
  ```
  Verify:
  - [ ] Status: `online`
  - [ ] Restarts: `0` (or low number)
  - [ ] Uptime: `> 1 minute`

- [ ] **Logs accessible**
  ```bash
  ssh REMOTE_HOST "pm2 logs hostamar --lines 10 --nostream"
  ```
  Should show Next.js startup messages, no errors

### Application Health
- [ ] **Port 3001 listening**
  ```bash
  ssh REMOTE_HOST "ss -tlnp | grep :3001 || sudo netstat -tlnp | grep :3001"
  # Should show next-server listening on 0.0.0.0:3001
  ```

- [ ] **Health endpoint responds**
  ```bash
  ssh REMOTE_HOST "curl -s http://127.0.0.1:3001/api/health | jq '.status'"
  # Expected: "ok"
  ```

- [ ] **Homepage loads**
  ```bash
  ssh REMOTE_HOST "curl -s http://127.0.0.1:3001 | grep -i hostamar"
  # Should return HTML with "Hostamar"
  ```

---

## 🌐 Deployment Phase 4: Nginx & SSL

### Nginx Installation
- [ ] **Nginx installed**
  ```bash
  ssh REMOTE_HOST "nginx -v"
  # Expected: nginx/1.18.0 or higher
  ```

- [ ] **Nginx running**
  ```bash
  ssh REMOTE_HOST "sudo systemctl status nginx | grep Active"
  # Expected: active (running)
  ```

### Nginx Configuration
- [ ] **Config file exists**
  ```bash
  ssh REMOTE_HOST "sudo cat /etc/nginx/sites-available/hostamar | head -5"
  ```

- [ ] **Config syntax valid**
  ```bash
  ssh REMOTE_HOST "sudo nginx -t"
  # Expected: syntax is ok, test is successful
  ```

- [ ] **Security headers present**
  ```bash
  curl -sI https://hostamar.com | grep -i strict-transport-security
  curl -sI https://hostamar.com | grep -i x-frame-options
  curl -sI https://hostamar.com | grep -i x-content-type-options
  curl -sI https://hostamar.com | grep -i referrer-policy
  curl -sI https://hostamar.com | grep -i permissions-policy
  # All should print a header line
  ```

- [ ] **Reverse proxy working**
  ```bash
  curl -s http://VM_EXTERNAL_IP | grep -i hostamar
  # Should return HTML (port 80 works)
  ```

### SSL Certificate
- [ ] **Certbot installed**
  ```bash
  ssh REMOTE_HOST "certbot --version"
  ```

- [ ] **Certificate issued**
  ```bash
  ssh REMOTE_HOST "sudo certbot certificates"
  ```
  Should show:
  - [ ] Certificate Name: `hostamar.com`
  - [ ] Domains: `hostamar.com www.hostamar.com`
  - [ ] Expiry Date: `> 80 days`

- [ ] **HTTPS redirect working**
  ```bash
  curl -I http://VM_EXTERNAL_IP
  # Expected: 301 Moved Permanently → https://
  ```

- [ ] **SSL certificate valid**
  ```bash
  curl -I https://VM_EXTERNAL_IP
  # Expected: 200 OK (if DNS pointing) or SSL error (if not)
  ```

---

## 🌍 Deployment Phase 5: DNS & Production

### DNS Configuration
- [ ] **Cloudflare account setup**
- [ ] **Domain added to Cloudflare**
- [ ] **A record created**
  - Type: `A`
  - Name: `@`
  - Content: `VM_EXTERNAL_IP`
  - Proxy: ✅ Proxied
  - TTL: Auto

- [ ] **WWW subdomain**
  - Type: `A`
  - Name: `www`
  - Content: `VM_EXTERNAL_IP`
  - Proxy: ✅ Proxied

- [ ] **SSL/TLS Mode**
  - Set to: **Full (strict)**

### DNS Propagation
- [ ] **DNS resolving**
  ```bash
  nslookup hostamar.com
  # Should return VM IP (or Cloudflare proxy IP)
  ```

- [ ] **HTTPS working**
  ```bash
  curl -I https://hostamar.com
  # Expected: 200 OK
  ```

- [ ] **Homepage accessible**
  ```bash
  curl -s https://hostamar.com | grep -i hostamar
  # Should return HTML
  ```

### Production Testing
- [ ] **Open in browser:** `https://hostamar.com`
- [ ] **Health check:** `https://hostamar.com/api/health`
  ```json
  {
    "status": "healthy",
    "database": { "connected": true }
  }
  ```

- [ ] **Signup page:** `https://hostamar.com/auth/signup`
- [ ] **Login page:** `https://hostamar.com/auth/signin`

### Create Test Account
- [ ] **Navigate to:** `https://hostamar.com/auth/signup`
- [ ] **Fill form:**
  - Name: `Test User`
  - Email: `test@example.com`
  - Password: `Test@1234`
  - Business Name: `Test Business`
  - Industry: `Retail`
- [ ] **Submit and verify redirect to `/dashboard`**
- [ ] **Logout and login again** to verify persistence

---

## 🔍 Post-Deployment Verification

### Application Monitoring
- [ ] **PM2 monitoring**
  ```bash
  ssh REMOTE_HOST "pm2 monit"
  # Shows real-time CPU/Memory
  ```

- [ ] **Check for restarts**
  ```bash
  ssh REMOTE_HOST "pm2 info hostamar | grep restarts"
  # Should be 0 or very low
  ```

- [ ] **Review logs for errors**
  ```bash
  ssh REMOTE_HOST "pm2 logs hostamar --err --lines 50"
  # Should be empty or no critical errors
  ```


### Monitoring & Maintenance

- [ ] **Install uptime + TLS checks**

  ```bash
  ssh REMOTE_HOST "cd ~/hostamar-platform/deploy/monitoring && chmod +x *.sh && sudo ./install_cron.sh --domain hostamar.com --health-url https://hostamar.com/api/health --pm2-user $USER --pm2-logs /home/$USER/.pm2/logs/*.log"
  ssh REMOTE_HOST "sudo tail -n 50 /var/log/hostamar/cron_task.log"
  ```

- [ ] **PM2 autostart (oneshot) enabled**

  ```bash
  ssh REMOTE_HOST "systemctl is-enabled pm2-$USER && systemctl --no-pager --full status pm2-$USER"
  # Expected: enabled; active (exited)
  ```

- [ ] **PM2 autostart resilience test (optional)**

  ```bash
  ssh REMOTE_HOST "pm2 kill && sudo systemctl restart pm2-$USER && pm2 ls"
  # Expected: hostamar online after restart
  ```

- [ ] **Certbot renew dry-run**

  ```bash
  ssh REMOTE_HOST "sudo certbot renew --dry-run"
  # Expected: simulated renewal succeeded
  ```

### System Resources
- [ ] **Disk space sufficient**
  ```bash
  ssh REMOTE_HOST "df -h | grep -E '^/dev'"
  # Should have > 2GB free
  ```

- [ ] **Memory not exhausted**
  ```bash
  ssh REMOTE_HOST "free -h"
  # Available > 500MB
  ```

- [ ] **CPU not overloaded**
  ```bash
  ssh REMOTE_HOST "uptime"
  # Load average < number of CPUs
  ```

### Security
- [ ] **Firewall rules restrictive**
  ```bash
  gcloud compute firewall-rules list --format="table(name,allowed)"
  ```
  Should ONLY allow:
  - [ ] Port 22 from trusted IPs (or all if needed)
  - [ ] Port 80 from 0.0.0.0/0
  - [ ] Port 443 from 0.0.0.0/0

- [ ] **SSH keys secure**
  ```bash
  ssh REMOTE_HOST "ls -la ~/.ssh/authorized_keys"
  # Should be 600 permissions
  ```

- [ ] **Environment variables not exposed**
  ```bash
  curl -s https://hostamar.com/api/health | grep -i "NEXTAUTH_SECRET"
  # Should NOT appear (check health endpoint doesn't leak secrets)
  ```

---

## 📊 Performance Baseline

### Response Times
- [ ] **Homepage load time**
  ```bash
  curl -o /dev/null -s -w '%{time_total}\n' https://hostamar.com
  # Target: < 2 seconds
  ```

- [ ] **API health check**
  ```bash
  curl -o /dev/null -s -w '%{time_total}\n' https://hostamar.com/api/health
  # Target: < 0.5 seconds
  ```

### Load Testing (Optional)
- [ ] **Install ab (Apache Bench)**
  ```bash
  sudo apt install apache2-utils  # On Linux
  ```

- [ ] **Run basic load test**
  ```bash
  ab -n 100 -c 10 https://hostamar.com/api/health
  ```
  Verify:
  - [ ] No failed requests
  - [ ] Mean response time < 500ms

---

## 🆘 Rollback Plan (If Issues Found)

### Quick Rollback
- [ ] **Stop application**
  ```bash
  ssh REMOTE_HOST "pm2 stop hostamar"
  ```

- [ ] **Restore previous version**
  ```bash
  # From local git
  git checkout HEAD~1
  rsync -avzP --exclude 'node_modules' ./ REMOTE_HOST:~/hostamar-platform/
  ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"
  ```

### Emergency Contacts
- [ ] **Team notified** via Slack/Email
- [ ] **Incident log created**
- [ ] **Root cause analysis** scheduled

---

## ✅ Final Sign-Off

### Documentation
- [ ] **README.md updated** with production URL
- [ ] **Environment variables documented**
- [ ] **Deployment runbook reviewed**
- [ ] **Monitoring alerts configured** (future)

### Team Handoff
- [ ] **Deployment demo** completed
- [ ] **Access credentials** shared securely
- [ ] **Maintenance schedule** defined
- [ ] **Backup strategy** implemented (future)

### Business Readiness
- [ ] **Payment gateway** integrated (pending)
- [ ] **Email notifications** working (pending)
- [ ] **Terms of Service** published
- [ ] **Privacy Policy** published
- [ ] **Support channels** established

---

## 📈 Next Steps

Once all checklist items are ✅:

1. **Monitor for 24 hours** - Watch logs, CPU, memory
2. **Announce soft launch** - Invite beta users
3. **Set up monitoring** - Implement error tracking (Sentry)
4. **Configure backups** - Daily database backups
5. **Scale as needed** - Upgrade VM if traffic increases

---

## 📞 Support Resources

- **Deployment Guide:** `deploy/DEPLOYMENT_GUIDE.md`
- **Cheatsheet:** `deploy/CHEATSHEET.md`
- **Architecture:** `deploy/ARCHITECTURE.md`
- **Troubleshooting:** Section 7 of DEPLOYMENT_GUIDE.md

---

**আপনার রিপোর্টের সব ধাপ এই checklist-এ cover করা হয়েছে। ✅**

*Print this checklist and check off items as you complete them!*

---

## 🔐 SSH Access Recovery (Windows)

Use these steps if `ssh` or `scp` fail with `Permission denied (publickey)`.

- Generate a keypair (if you don’t have one):

  ```powershell
  ssh-keygen -t ed25519 -C "romel@hostamar" -f "$HOME\.ssh\id_ed25519"
  ```

- Add key to OS Login (recommended if OS Login is enabled):

  ```powershell
  gcloud compute os-login ssh-keys add --key-file="$HOME\.ssh\id_ed25519.pub"
  ```

- OR add key to instance metadata for Linux user `romel` (if OS Login is disabled):

  ```powershell
  $pub = Get-Content "$HOME\.ssh\id_ed25519.pub"
  $line = "romel:$pub"
  $tf = New-TemporaryFile
  $line | Out-File -FilePath $tf -Encoding ascii -NoNewline
  gcloud compute instances add-metadata hostamar --zone=us-central1-a --metadata-from-file=ssh-keys="$(($tf).FullName)"
  ```

- Connect with the correct username:
  - If OS Login is enabled, your POSIX username is shown by `gcloud compute os-login ssh-keys add` output (e.g., `romelraisul_gmail_com`):

    ```powershell
    ssh -i "$HOME\.ssh\id_ed25519" romelraisul_gmail_com@35.232.209.133
    ```

  - If using instance metadata for user `romel`:

    ```powershell
    ssh -i "$HOME\.ssh\id_ed25519" romel@35.232.209.133
    ```

- gcloud alternatives (auto-manages keys):

  ```powershell
  gcloud compute ssh hostamar --zone=us-central1-a
  # If needed over IAP:
  gcloud compute ssh hostamar --zone=us-central1-a --tunnel-through-iap
  ```

- After access is restored, transfer monitoring and install:

  ```powershell
  # Ensure target directory exists (as the target user)
  ssh -i "$HOME\.ssh\id_ed25519" romel@35.232.209.133 "mkdir -p ~/hostamar-platform/deploy"

  # Copy monitoring
  scp -i "$HOME\.ssh\id_ed25519" -r .\deploy\monitoring romel@35.232.209.133:/home/romel/hostamar-platform/deploy/

  # Install on VM
  ssh -i "$HOME\.ssh\id_ed25519" romel@35.232.209.133 "cd ~/hostamar-platform/deploy/monitoring; chmod +x *.sh; sudo ./install_cron.sh --domain hostamar.com --health-url https://hostamar.com/api/health --pm2-user romel --pm2-logs '/home/romel/.pm2/logs/*.log'; sudo tail -n 50 /var/log/hostamar/cron_task.log"
  ```

- Common pitfalls:
  - Mistyped IP (use `35.232.209.133`).
  - Using `romel` when OS Login is enforced (use your OS Login username instead).
  - `gcloud compute ssh` on Windows uses PuTTY/Plink; `-vvv` isn’t supported the same way.
  - `gcloud compute scp` requires the remote directory to exist first.

Host hostamar
    HostName 35.232.209.133
    User romel
    IdentityFile C:\Users\romel\.ssh\id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 10
    ServerAliveCountMax 3
