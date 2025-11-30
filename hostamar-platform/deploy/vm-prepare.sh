#!/bin/bash
# GCP VM Preparation Script
# Run this on hybrid-cloud-gateway VM to install all dependencies

set -e

echo "🚀 Preparing GCP VM for Hostamar Platform deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install Node.js 20 LTS
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "✓ Node.js already installed: $(node --version)"
fi

# Install PM2
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2 process manager..."
    sudo npm install -g pm2
    sudo pm2 startup systemd -u $USER --hp $HOME
else
    echo "✓ PM2 already installed: $(pm2 --version)"
fi

# Install PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
else
    echo "✓ PostgreSQL already installed"
fi

# Create database and user for hostamar
echo "📦 Setting up PostgreSQL database..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'hostamar'" | grep -q 1 || \
sudo -u postgres psql <<EOF
CREATE DATABASE hostamar;
CREATE USER hostamar_user WITH PASSWORD 'hostamar_secure_2025';
GRANT ALL PRIVILEGES ON DATABASE hostamar TO hostamar_user;
ALTER DATABASE hostamar OWNER TO hostamar_user;
\q
EOF

echo "✓ PostgreSQL database 'hostamar' ready"

# Install Nginx
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt-get install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
else
    echo "✓ Nginx already installed"
fi

# Install Certbot for SSL
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot (Let's Encrypt)..."
    sudo apt-get install -y certbot python3-certbot-nginx
else
    echo "✓ Certbot already installed"
fi

# Create deployment directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/hostamar
sudo chown -R $USER:$USER /var/www/hostamar

# Install rsync if not present
if ! command -v rsync &> /dev/null; then
    echo "📦 Installing rsync..."
    sudo apt-get install -y rsync
fi

echo ""
echo "✅ VM preparation complete!"
echo ""
echo "Installed:"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"
echo "  - PM2: $(pm2 --version)"
echo "  - PostgreSQL: $(psql --version | head -n1)"
echo "  - Nginx: $(nginx -v 2>&1)"
echo "  - Certbot: $(certbot --version)"
echo ""
echo "Next step: Run deployment script from your local machine"
