# 🚀 Hostamar Platform - GCP Mumbai Deployment

আপনার রিপোর্টের সম্পূর্ণ implementation সহ production-ready deployment solution।

## 📦 এখন কী কী তৈরি হয়েছে

### ✅ Deployment Scripts
- **`deploy/gcp-mumbai-deploy.sh`** - Automated bash deployment script
- **`deploy/deploy.py`** - Python alternative (same functionality)
- **`deploy/nginx-setup.sh`** - Nginx + SSL configuration script

### ✅ Documentation
- **`deploy/DEPLOYMENT_GUIDE.md`** - সম্পূর্ণ step-by-step guide (AI prompts সহ)
- **`deploy/CHEATSHEET.md`** - Quick reference commands
- **`deploy/package.json`** - Deployment npm scripts

### ✅ Configuration Files
- **`deploy/ssh-config-template`** - VS Code Remote SSH config
- **`.vscode/remote-settings.json`** - Remote development settings
- **`app/api/health/route.ts`** - Health check endpoint

---

## 🎯 Quick Start (3টি পদ্ধতি)

### Method 1: Automated Script (সবচেয়ে সহজ) ⭐

```bash
# 1. Edit configuration
# Open deploy/gcp-mumbai-deploy.sh
# Update: VM_NAME, ZONE, PROJECT_ID

# 2. Run
cd c:/Users/romel/OneDrive/Documents/aiauto/hostamar-platform
bash deploy/gcp-mumbai-deploy.sh
```

**এটি automatically করবে:**
- ✅ gcloud authentication check
- ✅ SSH configuration
- ✅ Code upload (rsync)
- ✅ Environment setup
- ✅ Database migration
- ✅ Production build
- ✅ PM2 process manager
- ✅ Application start

---

### Method 2: Python Script

```bash
# 1. Edit deploy/deploy.py
# Update VM_CONFIG dictionary

# 2. Run
python deploy/deploy.py
```

---

### Method 3: AI Agent (VS Code Copilot)

আপনার রিপোর্টের exact workflow follow করে:

#### Step 1: SSH Configuration
```
প্রম্পট: Configure SSH to my GCP VM "mumbai-instance-1" in "asia-south1-a" zone using gcloud.
```

#### Step 2: Code Upload
```
প্রম্পট: Upload hostamar-platform to VM using rsync. 
Exclude node_modules, .git, .next. Use compression and show progress.
```

#### Step 3: Environment Setup
```
প্রম্পট: SSH to the VM and setup Node.js 20, run npm install, 
create production .env, run prisma db push, and build the app.
```

#### Step 4: PM2 Setup
```
প্রম্পট: Install PM2, start the app with auto-restart on crashes and VM reboots.
```

#### Step 5: Nginx + SSL
```
প্রম্পট: Configure Nginx reverse proxy for port 3000 and setup Let's Encrypt SSL for hostamar.com.
```

পুরো AI conversation flow **`deploy/DEPLOYMENT_GUIDE.md`**-এ আছে।

---

## 🔧 Prerequisites

### Local Machine
```bash
# gcloud CLI
gcloud --version
# Not installed? https://cloud.google.com/sdk/docs/install

# Authentication
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### GCP VM Requirements
- **Region:** asia-south1 (Mumbai)
- **OS:** Ubuntu 20.04+ or Debian 11+
- **Firewall:** Allow TCP 22, 80, 443
- **Disk:** 20GB minimum

### Domain (optional)
- Cloudflare account
- Domain pointed to VM IP

---

## 📊 Architecture

```
┌─────────────────┐
│  Local VS Code  │
│   (AI Agent)    │
└────────┬────────┘
         │ gcloud config-ssh
         ▼
┌─────────────────┐
│   SSH Tunnel    │
└────────┬────────┘
         │ rsync (code upload)
         ▼
┌─────────────────────────────────────┐
│  GCP Mumbai VM (asia-south1-a)      │
│                                     │
│  ┌──────────────┐                  │
│  │   Node.js    │                  │
│  │  (Next.js)   │                  │
│  │   Port 3000  │                  │
│  └──────┬───────┘                  │
│         │                           │
│  ┌──────▼───────┐                  │
│  │     PM2      │ ← Process Manager│
│  └──────────────┘                  │
│         │                           │
│  ┌──────▼───────┐                  │
│  │    Nginx     │ ← Port 80/443    │
│  │ Reverse Proxy│                  │
│  └──────┬───────┘                  │
│         │                           │
│  ┌──────▼───────┐                  │
│  │ Let's Encrypt│ ← SSL Certificate│
│  └──────────────┘                  │
└─────────┬───────────────────────────┘
          │
          ▼
   ┌──────────────┐
   │  Cloudflare  │
   │     DNS      │
   └──────────────┘
          │
          ▼
   🌐 https://hostamar.com
```

---

## 🚦 Post-Deployment Steps

### 1. Verify Application
```bash
# Get VM IP
gcloud compute instances describe mumbai-instance-1 \
    --zone=asia-south1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Test endpoints
curl http://VM_IP:3000
curl http://VM_IP:3000/api/health
```

### 2. Setup Nginx + SSL
```bash
# SSH to VM
ssh mumbai-instance-1.asia-south1-a.YOUR_PROJECT_ID

# Run nginx setup
cd ~/hostamar-platform/deploy
chmod +x nginx-setup.sh
./nginx-setup.sh
```

### 3. Configure DNS (Cloudflare)
1. Copy VM External IP
2. Cloudflare Dashboard → DNS
3. Add A records:
   - `@` → `VM_IP` (Proxied ✅)
   - `www` → `VM_IP` (Proxied ✅)
4. SSL/TLS Mode: **Full (strict)**

### 4. Enable Firewall
```bash
gcloud compute firewall-rules create allow-http --allow tcp:80
gcloud compute firewall-rules create allow-https --allow tcp:443
```

---

## 🛠️ Day-to-Day Operations

### Code Update & Redeploy
```bash
# Sync changes
rsync -avzP --exclude 'node_modules' \
    ./ REMOTE_HOST:~/hostamar-platform/

# Rebuild & restart
ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"
```

### View Logs
```bash
ssh REMOTE_HOST "pm2 logs hostamar --lines 100"
```

### Restart Application
```bash
ssh REMOTE_HOST "pm2 restart hostamar"
```

### Database Migration
```bash
ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma db push"
```

সব commands **`deploy/CHEATSHEET.md`**-এ আছে।

---

## 🎨 VS Code Remote Development

### Setup
1. Install extension: **Remote - SSH**
2. Press `F1` → `Remote-SSH: Connect to Host`
3. Enter: `mumbai-instance-1.asia-south1-a.YOUR_PROJECT_ID`
4. Open folder: `/home/romelraisul/hostamar-platform`

এখন আপনি সরাসরি VM-এ code edit করতে পারবেন!

### Optimized Settings
`.vscode/remote-settings.json` already configured:
- ✅ Extended connection timeout (60s)
- ✅ Auto file watcher exclusions
- ✅ Essential extensions auto-install

---

## 🔍 Monitoring & Debugging

### Health Check
```bash
curl http://localhost:3000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-29T...",
  "database": {
    "connected": true,
    "customers": 0
  },
  "environment": {
    "nodeEnv": "production",
    "nextAuthUrl": "https://hostamar.com"
  }
}
```

### PM2 Monitoring
```bash
ssh REMOTE_HOST "pm2 monit"  # Real-time dashboard
ssh REMOTE_HOST "pm2 status" # Status table
```

### System Resources
```bash
ssh REMOTE_HOST "free -h"     # Memory
ssh REMOTE_HOST "df -h"       # Disk space
ssh REMOTE_HOST "htop"        # CPU & processes
```

---

## 🆘 Troubleshooting

### Problem: SSH Connection Failed
```bash
# Check VM status
gcloud compute instances describe mumbai-instance-1 --zone=asia-south1-a

# Check firewall
gcloud compute firewall-rules list

# Re-configure SSH
gcloud compute config-ssh
```

### Problem: App Not Accessible
```bash
# Check PM2
ssh REMOTE_HOST "pm2 status"

# Check port
ssh REMOTE_HOST "sudo netstat -tulpn | grep :3000"

# Check logs
ssh REMOTE_HOST "pm2 logs hostamar --err --lines 50"
```

### Problem: Database Error
```bash
# Check database file
ssh REMOTE_HOST "ls -lh ~/hostamar-platform/prod.db"

# Re-run migration
ssh REMOTE_HOST "cd ~/hostamar-platform && npx prisma db push --force-reset"
```

সব troubleshooting scenarios **`deploy/DEPLOYMENT_GUIDE.md`** Section 7-এ আছে।

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `deploy/DEPLOYMENT_GUIDE.md` | Complete step-by-step guide with AI prompts |
| `deploy/CHEATSHEET.md` | Quick command reference |
| `deploy/gcp-mumbai-deploy.sh` | Automated bash deployment script |
| `deploy/deploy.py` | Python deployment script |
| `deploy/nginx-setup.sh` | Nginx + SSL configuration |
| `deploy/ssh-config-template` | SSH config template |
| `.vscode/remote-settings.json` | VS Code remote optimization |
| `app/api/health/route.ts` | Health check endpoint |

---

## 🎓 Technical Highlights (আপনার রিপোর্ট থেকে)

### Why Rsync over SCP?
- ✅ Delta encoding (শুধু changes transfer)
- ✅ Resume capability (connection lost হলে)
- ✅ Bandwidth savings (~70% less data)
- ✅ Smart filtering (node_modules exclude)

### Why gcloud config-ssh?
- ✅ Automatic SSH key management
- ✅ Dynamic IP handling
- ✅ No manual key copying
- ✅ Metadata server integration

### Why PM2?
- ✅ Auto-restart on crash
- ✅ Cluster mode (multi-core)
- ✅ Zero-downtime reload
- ✅ Log management
- ✅ Startup script generation

### Latency Optimization
- Connection timeout: 60s (Mumbai-specific)
- ServerAliveInterval: 60s
- VS Code local type prediction
- Nginx static file caching

---

## 🔐 Security Checklist

- [ ] `.env` never committed to Git
- [ ] SSH keys protected (600 permissions)
- [ ] Firewall rules restrictive (only 22, 80, 443)
- [ ] SSL certificate valid (Let's Encrypt)
- [ ] Database not publicly accessible
- [ ] PM2 running as non-root user
- [ ] Nginx security headers enabled

---

## 🚀 Performance Tips

**Next.js Caching:**
```bash
# Add to .env on VM
NEXT_CACHE_HANDLER="filesystem"
```

**PM2 Cluster Mode:**
```bash
pm2 start npm --name hostamar -i max -- start
```

**Nginx Static Caching:**
Already configured in `nginx-setup.sh`

---

## 📞 Support

**Quick Commands:**
- View todo: `cat deploy/DEPLOYMENT_GUIDE.md | grep "Step"`
- Emergency stop: `ssh REMOTE_HOST "pm2 stop hostamar"`
- Full logs: `ssh REMOTE_HOST "pm2 logs hostamar"`

**AI Agent Prompts:**
সব AI prompts **`deploy/DEPLOYMENT_GUIDE.md`** Section 6-এ আছে।

---

## 🎯 Next Steps

1. **Run Deployment:**
   ```bash
   bash deploy/gcp-mumbai-deploy.sh
   ```

2. **Setup Nginx:**
   ```bash
   ssh REMOTE_HOST "./hostamar-platform/deploy/nginx-setup.sh"
   ```

3. **Configure DNS:**
   Point `hostamar.com` to VM IP

4. **Test Production:**
   ```bash
   curl https://hostamar.com/api/health
   ```

---

**আপনার রিপোর্টের সব technical requirements implement করা হয়েছে। Deployment শুরু করতে পারেন!** 🚀

---

*Last Updated: November 29, 2025*  
*Based on: "Google Cloud Platform-এ বিদ্যমান মুম্বাই অঞ্চলের ভার্চুয়াল মেশিনে VS Code AI এজেন্ট ব্যবহার করে কোড ডিপ্লয়মেন্ট এবং রিমোট ডেভেলপমেন্টের পূর্ণাঙ্গ টেকনিক্যাল রিপোর্ট"*
