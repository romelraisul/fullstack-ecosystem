# 🚀 GCP Mumbai Deployment - Quick Reference

## 🎯 One-Command Deployment
```bash
cd c:/Users/romel/OneDrive/Documents/aiauto/hostamar-platform
bash deploy/gcp-mumbai-deploy.sh
```

## 🔧 Essential Commands

### SSH Access
```bash
# Auto-configure SSH
gcloud compute config-ssh

# Connect
ssh mumbai-instance-1.asia-south1-a.YOUR_PROJECT_ID

# Or use alias (add to ~/.ssh/config)
ssh mumbai-hostamar
```

### Code Upload
```bash
# Full sync
rsync -avzP --exclude 'node_modules' --exclude '.git' \
    ./ REMOTE_HOST:~/hostamar-platform/

# Quick update (changed files only)
rsync -avzP --delete --exclude 'node_modules' \
    ./ REMOTE_HOST:~/hostamar-platform/
```

### Remote Operations
```bash
# View logs
ssh REMOTE_HOST "pm2 logs hostamar --lines 100"

# Restart app
ssh REMOTE_HOST "pm2 restart hostamar"

# Check status
ssh REMOTE_HOST "pm2 status"

# Rebuild
ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"
```

### Database Operations
```bash
# Migrate schema
ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma db push"

# Generate Prisma Client
ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma generate"

# View database
ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma studio"
```

### Nginx Commands
```bash
# Test config
ssh REMOTE_HOST "sudo nginx -t"

# Reload
ssh REMOTE_HOST "sudo systemctl reload nginx"

# View logs
ssh REMOTE_HOST "sudo tail -f /var/log/nginx/hostamar.com_error.log"
```

### SSL Certificate
```bash
# Install SSL
ssh REMOTE_HOST "sudo certbot --nginx -d hostamar.com -d www.hostamar.com"

# Renew (test)
ssh REMOTE_HOST "sudo certbot renew --dry-run"
```

### Firewall
```bash
# Allow HTTP/HTTPS
gcloud compute firewall-rules create allow-http --allow tcp:80
gcloud compute firewall-rules create allow-https --allow tcp:443

# List rules
gcloud compute firewall-rules list
```

### Monitoring
```bash
# Disk space
ssh REMOTE_HOST "df -h"

# Memory usage
ssh REMOTE_HOST "free -h"

# Running processes
ssh REMOTE_HOST "htop"

# Port status
ssh REMOTE_HOST "sudo netstat -tulpn | grep :3000"
```

## 🤖 AI Agent Prompts (VS Code Copilot)

### Initial Setup
```
Configure SSH to my GCP VM named "mumbai-instance-1" in zone "asia-south1-a" using gcloud.
```

### Code Deployment
```
Upload my current directory to the VM at ~/hostamar-platform using rsync. 
Exclude node_modules, .git, .next. Show progress and use compression.
```

### Environment Setup
```
SSH to the VM and:
1. Check if Node.js 20.x is installed, install if missing
2. Run npm install in ~/hostamar-platform
3. Create production .env file
4. Run prisma db push
5. Build Next.js app
```

### PM2 Setup
```
Install PM2 globally on the VM, start my Next.js app with auto-restart, 
and configure it to survive VM reboots.
```

### Nginx + SSL
```
On the remote VM, install Nginx, configure reverse proxy for port 3000, 
and setup Let's Encrypt SSL for hostamar.com.
```

### Troubleshooting
```
I can't connect to my VM via SSH. Check firewall rules and help me debug.
```

```
The app shows as "online" in pm2 but I can't access it in browser. Debug networking.
```

```
Files I save on the remote VM show "permission denied". Fix ownership.
```

## 📊 Health Check URLs

After deployment, test these:

- `http://VM_IP:3000` - Direct app access
- `http://VM_IP:3000/api/auth/signin` - Auth check
- `http://VM_IP:3000/api/health` - Health endpoint (create this!)
- `http://hostamar.com` - Production URL (after DNS)

## 🔄 Update Workflow

1. **Make changes locally**
2. **Sync to VM:**
   ```bash
   rsync -avzP --exclude 'node_modules' ./ REMOTE_HOST:~/hostamar-platform/
   ```
3. **Rebuild & restart:**
   ```bash
   ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"
   ```
4. **Verify:**
   ```bash
   ssh REMOTE_HOST "pm2 logs hostamar --lines 50"
   ```

## 🆘 Emergency Commands

**Stop everything:**
```bash
ssh REMOTE_HOST "pm2 stop hostamar && sudo systemctl stop nginx"
```

**Backup database:**
```bash
ssh REMOTE_HOST "cd ~/hostamar-platform && tar -czf ~/backup-$(date +%Y%m%d).tar.gz prod.db"
```

**Rollback code:**
```bash
# Local: checkout previous commit
git checkout HEAD~1

# Sync
rsync -avzP --delete ./ REMOTE_HOST:~/hostamar-platform/

# Rebuild
ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"
```

**Clean reinstall:**
```bash
ssh REMOTE_HOST "cd ~/hostamar-platform && rm -rf node_modules .next && npm install && npm run build && pm2 restart hostamar"
```

## 📁 File Locations on VM

- **App:** `/home/romelraisul/hostamar-platform`
- **Database:** `/home/romelraisul/hostamar-platform/prod.db`
- **PM2 logs:** `~/.pm2/logs/`
- **Nginx config:** `/etc/nginx/sites-available/hostamar.com`
- **SSL certs:** `/etc/letsencrypt/live/hostamar.com/`

## 🎯 Performance Tips

**Enable Next.js output cache:**
```bash
# Add to .env on VM
NEXT_CACHE_HANDLER="filesystem"
```

**PM2 Cluster mode (use all CPU cores):**
```bash
ssh REMOTE_HOST "pm2 delete hostamar && pm2 start npm --name hostamar -i max -- start"
```

**Nginx caching:**
```nginx
# Add to Nginx config
location /_next/static {
    proxy_cache STATIC;
    proxy_pass http://localhost:3000;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

## 🌐 DNS Setup (Cloudflare)

1. Get VM IP: `gcloud compute instances describe mumbai-instance-1 --zone=asia-south1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'`
2. Cloudflare Dashboard → DNS
3. Add records:
   - Type: `A`, Name: `@`, Content: `VM_IP`, Proxy: ✅
   - Type: `A`, Name: `www`, Content: `VM_IP`, Proxy: ✅
4. SSL/TLS Mode: **Full (strict)**

## 🔍 Logs & Debugging

**Application logs:**
```bash
ssh REMOTE_HOST "pm2 logs hostamar --lines 200"
```

**Nginx access logs:**
```bash
ssh REMOTE_HOST "sudo tail -f /var/log/nginx/hostamar.com_access.log"
```

**System logs:**
```bash
ssh REMOTE_HOST "sudo journalctl -u nginx -n 50"
```

**Real-time monitoring:**
```bash
# Install on VM first: sudo apt install htop
ssh REMOTE_HOST "htop"
```

---

**সব কমান্ড এক জায়গায়! Bookmark this file. 🔖**
