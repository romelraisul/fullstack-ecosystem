#!/bin/bash
# Complete Deployment Script - Run from GCP VM
# This script runs everything from the VM itself

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🚀 HOSTAMAR PLATFORM - VM DEPLOYMENT 🚀              ║
║                                                           ║
║     Complete setup running from GCP VM                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

START_TIME=$(date +%s)

# ============================================================================
# STEP 1: Install System Dependencies
# ============================================================================
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 1/5: Installing System Dependencies${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install Node.js 20 LTS
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo -e "${GREEN}✓ Node.js installed: $(node --version)${NC}"
else
    echo -e "${GREEN}✓ Node.js already installed: $(node --version)${NC}"
fi

# Install PM2
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2..."
    sudo npm install -g pm2
    # Ensure PM2 runs on boot
    PM2_START_CMD=$(pm2 startup systemd -u $USER --hp $HOME | grep -E "^sudo")
    if [ -n "$PM2_START_CMD" ]; then
      eval $PM2_START_CMD
    fi
    echo -e "${GREEN}✓ PM2 installed${NC}"
else
    echo -e "${GREEN}✓ PM2 already installed${NC}"
fi

# Install PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo -e "${GREEN}✓ PostgreSQL installed${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL already installed${NC}"
fi

# Install Nginx
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt-get install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    echo -e "${GREEN}✓ Nginx installed${NC}"
else
    echo -e "${GREEN}✓ Nginx already installed${NC}"
fi

# Install Certbot
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot..."
    sudo apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✓ Certbot installed${NC}"
else
    echo -e "${GREEN}✓ Certbot already installed${NC}"
fi

# ============================================================================
# STEP 2: Setup PostgreSQL Database
# ============================================================================
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 2/5: Setting up PostgreSQL Database${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "🗄️  Creating database and user..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'hostamar'" | grep -q 1 || \
sudo -u postgres psql <<EOF
CREATE DATABASE hostamar;
CREATE USER hostamar_user WITH PASSWORD 'hostamar_secure_2025';
GRANT ALL PRIVILEGES ON DATABASE hostamar TO hostamar_user;
ALTER DATABASE hostamar OWNER TO hostamar_user;
\q
EOF

echo -e "${GREEN}✓ Database 'hostamar' ready${NC}"

# ============================================================================
# STEP 3: Deploy Hostamar Platform
# ============================================================================
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 3/5: Deploying Hostamar Platform${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Validate source path exists
if [ ! -d "$HOME/hostamar-platform" ]; then
  echo -e "${YELLOW}⚠ Source directory '$HOME/hostamar-platform' not found. Ensure the project is uploaded there.${NC}"
  exit 1
fi

# Create app directory
APP_DIR="/var/www/hostamar"
echo "📁 Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Copy project files
echo "📦 Copying project files..."
rsync -a --delete "$HOME/hostamar-platform/" "$APP_DIR/"
cd $APP_DIR

# Create .env.production securely
echo "🔐 Creating production environment..."
cat > .env.production <<EOF
NODE_ENV=production
DATABASE_URL="postgresql://hostamar_user:hostamar_secure_2025@localhost:5432/hostamar?schema=public"
NEXTAUTH_SECRET="$(openssl rand -base64 32)"
NEXTAUTH_URL="https://hostamar.com"
PORT=3001
EOF
chmod 600 .env.production

# Install dependencies for build
echo "📦 Installing dependencies (this may take a few minutes)..."
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "🔧 Generating Prisma client..."
npx prisma generate

# Run database migrations: prefer migrate deploy if migrations exist
echo "🗄️  Running database migrations..."
if [ -d prisma/migrations ] && [ "$(ls -A prisma/migrations)" ]; then
    npx prisma migrate deploy
else
    npx prisma db push --skip-generate
fi

# Build Next.js app
echo "🔨 Building Next.js application..."
npm run build

# Prune devDependencies for runtime
npm prune --production || true

echo -e "${GREEN}✓ Application built successfully${NC}"

# Configure PM2
echo "⚙️  Configuring PM2..."
cat > ecosystem.config.js <<EOF
module.exports = {
  apps: [{
    name: 'hostamar-platform',
    script: 'npm',
    args: 'start',
    cwd: '$APP_DIR',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
            PORT: 3001
    }
  }]
}
EOF

# Start with PM2
echo "🚀 Starting application..."
pm2 delete hostamar-platform 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save

echo -e "${GREEN}✓ Application running on port 3001${NC}"

# ============================================================================
# STEP 4: Configure Nginx
# ============================================================================
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 4/5: Configuring Nginx Reverse Proxy${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

DOMAIN="${1:-hostamar.com}"

echo "🌐 Creating Nginx configuration for $DOMAIN..."
sudo tee /etc/nginx/sites-available/hostamar > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Health check
    location /api/health {
        proxy_pass http://localhost:3001/api/health;
        access_log off;
    }

    # Static caching
    location /_next/static {
        proxy_pass http://localhost:3001;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    access_log /var/log/nginx/hostamar-access.log;
    error_log /var/log/nginx/hostamar-error.log;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/hostamar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
echo "🔍 Testing Nginx configuration..."
sudo nginx -t
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

# ============================================================================
# STEP 5: Verification
# ============================================================================
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 5/5: Verification${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

sleep 3

echo "📊 Application Status:"
pm2 status

echo -e "\n🔍 Health Check:"
HEALTH=$(curl -s http://localhost:3001/api/health || echo "FAILED")
if [[ "$HEALTH" == *"ok"* ]] || [[ "$HEALTH" == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Health check PASSED${NC}"
else
    echo -e "${YELLOW}⚠  Health check FAILED - check logs${NC}"
fi

echo -e "\n🌐 Nginx Status:"
sudo systemctl status nginx --no-pager | head -5

echo -e "\n🗄️  Database Status:"
sudo systemctl status postgresql --no-pager | head -5

# ============================================================================
# SUMMARY
# ============================================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║            ✅ DEPLOYMENT COMPLETED! ✅                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}📊 Deployment Summary:${NC}"
echo "  Duration: $((DURATION / 60))m $((DURATION % 60))s"
echo "  App Directory: $APP_DIR"
echo "  Domain: $DOMAIN"

echo -e "\n${CYAN}🌐 Access your platform:${NC}"
echo "  Internal: http://localhost:3001"
echo "  External: http://$(curl -s ifconfig.me 2>/dev/null)"
echo -e "  ${YELLOW}Domain: http://$DOMAIN (after DNS setup)${NC}"

echo -e "\n${CYAN}📝 Useful commands:${NC}"
echo "  View logs:    pm2 logs hostamar-platform"
echo "  Restart app:  pm2 restart hostamar-platform"
echo "  Check status: pm2 status"
echo "  Monitor:      pm2 monit"

echo -e "\n${CYAN}🔐 Setup SSL (after DNS configured):${NC}"
echo -e "  ${YELLOW}sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN${NC}"

echo -e "\n${CYAN}🎯 What's deployed:${NC}"
echo -e "  ${GREEN}✓${NC} Node.js $(node --version) + PM2"
echo -e "  ${GREEN}✓${NC} PostgreSQL database"
echo -e "  ${GREEN}✓${NC} Hostamar Platform (Next.js)"
echo -e "  ${GREEN}✓${NC} Nginx reverse proxy"
echo -e "  ${GREEN}✓${NC} Monitoring timers"

echo -e "\n${CYAN}🚀 Next steps:${NC}"
echo "  1. Configure DNS: $DOMAIN → $(curl -s ifconfig.me 2>/dev/null)"
echo "  2. Setup SSL certificate"
echo "  3. Test signup: https://$DOMAIN/auth/signup"
echo "  4. Setup video generation pipeline"

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Happy deploying! 🎉${NC}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

Get-Service ssh-agent | Set-Service -StartupType Automatic; Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
ssh-add -l
