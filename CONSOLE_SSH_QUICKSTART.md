# Console SSH Quick Start Guide

When direct SSH from your local machine fails, use Google Cloud Console's browser-based SSH.

## Method 1: Console SSH Button (Recommended)

1. **Open GCP Console**: https://console.cloud.google.com/compute/instances?project=arafat-468807
2. **Find your VM**: Locate `hostamar` in the instance list
3. **Click "SSH"**: The SSH button is in the "Connect" column
4. **Browser terminal opens**: You're now directly on the VM

## Method 2: Cloud Shell + gcloud

If Console SSH button isn't working:

```bash
# In Cloud Shell (top-right icon in GCP Console)
gcloud compute ssh hostamar --zone us-central1-a --project arafat-468807
```

## Method 3: Serial Console (Emergency Access)

If both SSH methods fail (network or sshd issues):

1. **Navigate to VM details**: Click on `hostamar` instance name
2. **Go to "Logs" section**: Scroll down in left sidebar
3. **Click "Serial port 1 (console)"**: Opens low-level console
4. **Press Enter**: May need to press Enter a few times to get login prompt
5. **Login**: Use your username (e.g., `romelraisul_gmail_com`)

> **Note**: You may need a password set for serial console access. If not configured, use Console SSH to set one first:
> ```bash
> sudo passwd your_username
> ```

## Deploy Hostamar (Once Connected)

Run these commands in any of the above terminals:

### 1. Fetch Deploy Script

```bash
mkdir -p ~/scripts
curl -fsSL https://raw.githubusercontent.com/romelraisul/fullstack-ecosystem/main/scripts/deploy-all-from-vm.sh -o ~/scripts/deploy-all-from-vm.sh
chmod +x ~/scripts/deploy-all-from-vm.sh
```

### 2. Run Deployment

```bash
# Default: hostamar.com, monjilaktn/hostamar, main branch
bash ~/scripts/deploy-all-from-vm.sh

# Or customize:
bash ~/scripts/deploy-all-from-vm.sh yourdomain.com https://github.com/monjilaktn/hostamar.git main
```

### 3. Set Up Command Bridge

```bash
mkdir -p ~/command-bridge
cd ~/command-bridge
curl -fsSL https://raw.githubusercontent.com/romelraisul/fullstack-ecosystem/main/scripts/command-bridge/server.js -o server.js
npm init -y
npm install express
CB_TOKEN="YOUR_STRONG_SECRET_TOKEN" CB_PORT=8085 pm2 start server.js --name command-bridge
pm2 save
curl -s http://localhost:8085/healthz
```

## Diagnose SSH Issues (Optional)

If you want to fix direct SSH from your local machine:

```bash
# Run diagnostics on the VM
curl -fsSL https://raw.githubusercontent.com/romelraisul/fullstack-ecosystem/main/scripts/diagnose-ssh.sh | bash
```

This will check:
- SSH daemon status
- Firewall rules (internal)
- Network configuration
- SSH keys and permissions
- Recent authentication logs
- OS Login configuration

## Verify Deployment

```bash
# Check PM2 processes
pm2 status

# Test health endpoint
curl -s http://localhost:3001/api/health

# Check app logs
pm2 logs hostamar-platform --lines 50

# Test Nginx
sudo nginx -t
curl -s http://localhost
```

## Access Your App

- **Internal**: `http://localhost:3001`
- **External**: `http://VM_EXTERNAL_IP` (get IP: `curl ifconfig.me`)
- **Domain**: `http://yourdomain.com` (after DNS configured)

## Setup SSL (After DNS)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Troubleshooting

### Can't connect via Console SSH?
- Check VM is "Running" in Console
- Try stopping and starting the VM
- Check project-level SSH settings

### Deploy script fails?
- Check logs: `pm2 logs hostamar-platform`
- Verify repo is accessible: `git ls-remote https://github.com/monjilaktn/hostamar.git`
- Check disk space: `df -h`
- Check memory: `free -h`

### App not responding?
- Restart: `pm2 restart hostamar-platform`
- Check port: `sudo lsof -i :3001`
- Review logs: `pm2 logs hostamar-platform --err`

---

**Quick Links**
- GCP Console: https://console.cloud.google.com/compute/instances?project=arafat-468807
- Deploy Script: https://github.com/romelraisul/fullstack-ecosystem/blob/main/scripts/deploy-all-from-vm.sh
- Command Bridge: https://github.com/romelraisul/fullstack-ecosystem/blob/main/scripts/command-bridge/server.js
