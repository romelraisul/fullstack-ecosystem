#!/bin/bash
# Setup Let's Encrypt SSL certificate for Hostamar Platform

set -e

DOMAIN="${1:-hostamar.com}"
EMAIL="${2:-romelraisul@gmail.com}"

echo "🔐 Setting up SSL certificate for $DOMAIN..."

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update -qq
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Obtain and install certificate
echo "📜 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate installed successfully!"
    echo ""
    echo "Certificate details:"
    sudo certbot certificates
    echo ""
    echo "Auto-renewal is configured via systemd timer:"
    sudo systemctl status certbot.timer --no-pager
    echo ""
    echo "🌐 Your site is now available at:"
    echo "   https://$DOMAIN"
else
    echo ""
    echo "⚠️  SSL setup failed!"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure $DOMAIN DNS points to this server's IP"
    echo "  2. Check firewall allows port 80/443"
    echo "  3. Verify Nginx is running: sudo systemctl status nginx"
    echo ""
fi
