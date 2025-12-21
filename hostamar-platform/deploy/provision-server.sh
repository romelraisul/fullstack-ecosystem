#!/bin/bash
set -e

# Config
DB_USER="hostamar_user"
DB_PASS="hostamar_secure_2025"
DB_NAME="hostamar"
DOMAIN="hostamar.com"

echo "🚀 Starting Hostamar Server Provisioning..."

# 1. System Update & Swap (4GB)
echo "📦 Updating System..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
if [ ! -f /swapfile ]; then
    echo "💾 Creating 4GB Swap..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 2. Dependencies
echo "📦 Installing Dependencies..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs nginx postgresql postgresql-contrib certbot python3-certbot-nginx build-essential git

# 3. Global Node Packages
sudo npm install -g pm2

# 4. Database Setup
echo "🗄️ Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
\q
EOF

# 5. App Directory
echo "DIR Creating App Directory..."
sudo mkdir -p /var/www/hostamar
sudo chown -R $USER:$USER /var/www/hostamar

# 6. Nginx Config
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/hostamar > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/hostamar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "✅ Server Provisioned Successfully!"

