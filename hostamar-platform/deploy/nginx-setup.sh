#!/usr/bin/env bash
set -euo pipefail

# nginx-setup.sh
# Idempotent script to install & configure Nginx as reverse proxy for Next.js (port 3001)
# Includes optional Certbot issuance (run only AFTER DNS A records point to this VM).

SITE_DOMAIN="hostamar.com"
SITE_DOMAIN_WWW="www.hostamar.com"
NEXT_UPSTREAM="127.0.0.1:3001"
EMAIL="you@example.com"  # CHANGE BEFORE CERTBOT: set a valid address

echo "[INFO] Checking existing process on port 80..."
PORT80_PIDS=$(sudo lsof -t -i:80 || true)
if [[ -n "${PORT80_PIDS}" ]]; then
  echo "[WARN] Port 80 currently in use by PID(s): ${PORT80_PIDS}";
  echo "[INFO] Details:";
  sudo ss -tlnp | grep ':80' || true
  echo "[ACTION] Stop/disable the conflicting service (e.g., nghttpx) if NOT needed:";
  echo "        sudo systemctl stop nghttpx 2>/dev/null || true"
  echo "        sudo systemctl disable nghttpx 2>/dev/null || true"
  echo "[INFO] Re-run this script after freeing port 80 if Nginx start fails."
fi

echo "[INFO] Installing Nginx (if not present)..."
if ! command -v nginx >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y nginx
fi

echo "[INFO] Creating site configuration..."
sudo tee /etc/nginx/sites-available/hostamar <<'EOF' >/dev/null
map $http_upgrade $connection_upgrade {
  default upgrade;
  ''      close;
}

log_format hostamar_combined '$remote_addr - $remote_user [$time_local] '
                              '"$request" $status $body_bytes_sent '
                              '"$http_referer" "$http_user_agent" '
                              'rt=$request_time uct=$upstream_connect_time '
                              'urt=$upstream_response_time uht=$upstream_header_time';

server {
  listen 80 default_server;
  server_name ${SITE_DOMAIN} ${SITE_DOMAIN_WWW} _;

  # Security & tuning
  client_max_body_size 25m;
  keepalive_timeout 65;

  # Direct lightweight health endpoint
  location = /healthz {
    add_header Content-Type application/json;
    return 200 '{"status":"ok"}';
  }

  # Static asset caching (Next.js _next/static)
  location ^~ /_next/static/ {
    proxy_pass http://${NEXT_UPSTREAM};
    proxy_set_header Host $host;
    proxy_cache_revalidate on;
    proxy_cache_min_uses 2;
    expires 7d;
    add_header Cache-Control "public, max-age=604800, immutable";
  }

  # Main app proxy
  location / {
    proxy_pass http://${NEXT_UPSTREAM};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
  }

  access_log /var/log/nginx/hostamar.access.log hostamar_combined;
  error_log  /var/log/nginx/hostamar.error.log;
}
EOF

echo "[INFO] Enabling site..."
sudo ln -sf /etc/nginx/sites-available/hostamar /etc/nginx/sites-enabled/hostamar

echo "[INFO] Removing default site if present..."
if [[ -f /etc/nginx/sites-enabled/default ]]; then
  sudo rm -f /etc/nginx/sites-enabled/default
fi

echo "[INFO] Testing Nginx configuration..."
sudo nginx -t

echo "[INFO] Restarting Nginx..."
if ! sudo systemctl restart nginx; then
  echo "[ERROR] Nginx failed to start. Showing status & last journal lines:" >&2
  sudo systemctl status nginx --no-pager || true
  journalctl -xeu nginx.service --no-pager | tail -n 40 || true
  echo "[HINT] Ensure no other service binds to port 80 (e.g., nghttpx)." >&2
  exit 1
fi
sudo systemctl enable nginx

echo "[OK] Nginx reverse proxy active. Test with: curl -I http://$(curl -s ifconfig.me)" 

echo "[INFO] (Optional) Issue SSL certs after DNS points to this server."
cat <<CERT_INSTRUCTIONS
To issue certificates:
  1. Set Cloudflare A records for @ and www to this VM's IP.
  2. Wait for DNS propagation: nslookup ${SITE_DOMAIN}
  3. Run:
     sudo apt-get install -y certbot python3-certbot-nginx
     sudo certbot --nginx -d ${SITE_DOMAIN} -d ${SITE_DOMAIN_WWW} --redirect -m ${EMAIL} --agree-tos
  4. Verify:
     sudo certbot certificates
     curl -I https://${SITE_DOMAIN}
Renewal handled by systemd timer (check: systemctl list-timers | grep certbot).
CERT_INSTRUCTIONS

echo "[DONE] nginx-setup.sh complete."#!/bin/bash

# ==========================================
# Nginx + SSL Setup for Hostamar Platform
# ==========================================
# Run this ON THE REMOTE VM after initial deployment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOMAIN="hostamar.com"
APP_PORT="3000"

echo -e "${GREEN}=== Nginx + SSL Setup শুরু ===${NC}"

# === Step 1: Install Nginx ===
echo -e "\n${YELLOW}Step 1: Nginx install করা হচ্ছে...${NC}"
if ! command -v nginx &> /dev/null; then
    sudo apt update
    sudo apt install -y nginx
fi

sudo systemctl enable nginx
sudo systemctl start nginx
echo -e "${GREEN}✓ Nginx installed${NC}"

# === Step 2: Configure Nginx ===
echo -e "\n${YELLOW}Step 2: Nginx configuration করা হচ্ছে...${NC}"

sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log /var/log/nginx/${DOMAIN}_error.log;

    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Next.js static files
    location /_next/static {
        proxy_cache STATIC;
        proxy_pass http://localhost:$APP_PORT;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

# === Step 3: Setup Firewall ===
echo -e "\n${YELLOW}Step 3: Firewall rules করা হচ্ছে...${NC}"
if command -v ufw &> /dev/null; then
    sudo ufw allow 'Nginx Full'
    sudo ufw allow OpenSSH
    echo -e "${GREEN}✓ Firewall configured${NC}"
else
    echo "UFW not found, skipping firewall configuration"
    echo "Ensure GCP Firewall allows HTTP (80) and HTTPS (443)"
fi

# === Step 4: Install Certbot for SSL ===
echo -e "\n${YELLOW}Step 4: Let's Encrypt SSL setup...${NC}"
if ! command -v certbot &> /dev/null; then
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

echo -e "${YELLOW}SSL certificate পেতে চান? (y/n)${NC}"
echo "Note: Domain DNS অবশ্যই VM IP-তে point করতে হবে"
read -p "Continue? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMAIN \
        --redirect
    
    echo -e "${GREEN}✓ SSL certificate installed${NC}"
    echo "Certificate auto-renewal enabled"
else
    echo "SSL skipped. আপনি পরে চালাতে পারেন:"
    echo "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# === Summary ===
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Nginx + SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "🌐 Your site: http://$DOMAIN (or https:// if SSL enabled)"
echo "📊 Nginx status: sudo systemctl status nginx"
echo "📋 Nginx logs: sudo tail -f /var/log/nginx/${DOMAIN}_error.log"
echo "🔒 SSL renewal test: sudo certbot renew --dry-run"
echo ""
echo -e "${YELLOW}GCP Firewall Rules এখনো করা না থাকলে:${NC}"
echo "gcloud compute firewall-rules create allow-http --allow tcp:80"
echo "gcloud compute firewall-rules create allow-https --allow tcp:443"
