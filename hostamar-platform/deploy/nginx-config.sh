#!/bin/bash
# Configure Nginx as reverse proxy for Hostamar Platform

set -e

DOMAIN="${1:-hostamar.com}"
APP_PORT="3001"

echo "🌐 Configuring Nginx for $DOMAIN..."

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/hostamar > /dev/null <<EOF
# Hostamar Platform - Nginx Configuration
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Next.js app
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

    # Health check endpoint
    location /api/health {
        proxy_pass http://localhost:$APP_PORT/api/health;
        access_log off;
    }

    # Static files caching
    location /_next/static {
        proxy_pass http://localhost:$APP_PORT;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Logging
    access_log /var/log/nginx/hostamar-access.log;
    error_log /var/log/nginx/hostamar-error.log;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/hostamar /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🔍 Testing Nginx configuration..."
sudo nginx -t

# Reload Nginx
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ Nginx configured successfully!"
echo ""
echo "Next step: Setup SSL certificate"
echo "  sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
