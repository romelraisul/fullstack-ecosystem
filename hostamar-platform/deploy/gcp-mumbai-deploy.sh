#!/bin/bash

# ==========================================
# Hostamar Platform - GCP Mumbai Deployment
# ==========================================
# এই script টি আপনার রিপোর্টের সব ধাপ implement করে

set -e  # Error হলে stop করবে

# === Configuration ===
# আপনার VM details এখানে দিন:
VM_NAME="mumbai-instance-1"
ZONE="asia-south1-a"
PROJECT_ID="arafat-468807"  
REMOTE_USER="romelraisul"  # আপনার username
REMOTE_DIR="/home/$REMOTE_USER/hostamar-platform"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Hostamar Platform Deployment শুরু হচ্ছে ===${NC}"

# === Step 1: gcloud Authentication Check ===
echo -e "\n${YELLOW}Step 1: GCP Authentication যাচাই করা হচ্ছে...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}Error: আপনি gcloud-এ login করেননি${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Get project ID if empty
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}Error: কোনো project set করা নেই${NC}"
        echo "Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Authenticated with project: $PROJECT_ID${NC}"

# === Step 2: SSH Configuration (gcloud compute config-ssh) ===
echo -e "\n${YELLOW}Step 2: SSH configuration করা হচ্ছে...${NC}"
gcloud compute config-ssh --project="$PROJECT_ID"
HOST_ALIAS="$VM_NAME.$ZONE.$PROJECT_ID"
echo -e "${GREEN}✓ SSH configured. Host alias: $HOST_ALIAS${NC}"

# === Step 3: Test SSH Connection ===
echo -e "\n${YELLOW}Step 3: SSH connection test করা হচ্ছে...${NC}"
if ssh -o ConnectTimeout=10 "$HOST_ALIAS" "echo 'Connection successful'"; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}Error: VM-এ connect করতে পারছি না${NC}"
    echo "Check: 1) VM চালু আছে কিনা, 2) Firewall rules"
    exit 1
fi

# === Step 4: Create Remote Directory ===
echo -e "\n${YELLOW}Step 4: Remote directory তৈরি করা হচ্ছে...${NC}"
ssh "$HOST_ALIAS" "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✓ Directory created: $REMOTE_DIR${NC}"

# === Step 5: Upload Code using Rsync ===
echo -e "\n${YELLOW}Step 5: Code আপলোড হচ্ছে (rsync)...${NC}"
echo "এটি কিছু সময় নিতে পারে (প্রজেক্টের size অনুযায়ী)..."

# Go to project directory
cd "$(dirname "$0")/.."

rsync -avzP \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude '.next' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude '*.log' \
    --exclude '.env.local' \
    --exclude 'deploy' \
    ./ "$HOST_ALIAS:$REMOTE_DIR/"

echo -e "${GREEN}✓ Code upload সম্পূর্ণ${NC}"

# === Step 6: Setup Environment on VM ===
echo -e "\n${YELLOW}Step 6: VM-এ environment setup করা হচ্ছে...${NC}"

ssh "$HOST_ALIAS" bash <<'REMOTE_COMMANDS'
set -e

# Colors for remote output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd ~/hostamar-platform

echo -e "${YELLOW}6.1: Node.js version check...${NC}"
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
node --version
npm --version

echo -e "${YELLOW}6.2: npm install করা হচ্ছে...${NC}"
npm install --production

echo -e "${YELLOW}6.3: .env file তৈরি করা হচ্ছে...${NC}"
if [ ! -f .env ]; then
    cat > .env <<'EOF'
# Database
DATABASE_URL="file:./prod.db"

# NextAuth
NEXTAUTH_URL="https://hostamar.com"
NEXTAUTH_SECRET="hostamar-nextauth-secret-2025-production-key-12345"

# GitHub Models (if using)
GITHUB_TOKEN=""

# Azure AI Foundry
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://hostamar-resource.services.ai.azure.com/api/projects/hostamar"

# Node Environment
NODE_ENV="production"
PORT=3000
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo ".env already exists, skipping..."
fi

echo -e "${YELLOW}6.4: Prisma database setup...${NC}"
npx prisma generate
npx prisma db push --skip-generate

echo -e "${YELLOW}6.5: Production build করা হচ্ছে...${NC}"
npm run build

echo -e "${GREEN}✓ Environment setup complete${NC}"
REMOTE_COMMANDS

echo -e "${GREEN}✓ VM setup সম্পূর্ণ${NC}"

# === Step 7: Install PM2 ===
echo -e "\n${YELLOW}Step 7: PM2 process manager setup...${NC}"
ssh "$HOST_ALIAS" bash <<'PM2_SETUP'
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    sudo npm install -g pm2
fi
pm2 --version
PM2_SETUP

echo -e "${GREEN}✓ PM2 installed${NC}"

# === Step 8: Start Application ===
echo -e "\n${YELLOW}Step 8: Application start করা হচ্ছে...${NC}"
ssh "$HOST_ALIAS" bash <<'START_APP'
cd ~/hostamar-platform

# Stop existing process if running
pm2 delete hostamar 2>/dev/null || true

# Start with PM2
pm2 start npm --name "hostamar" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 startup (auto-restart on VM reboot)
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

pm2 list
START_APP

echo -e "${GREEN}✓ Application started with PM2${NC}"

# === Step 9: Get VM External IP ===
echo -e "\n${YELLOW}Step 9: VM External IP খুঁজছি...${NC}"
EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --project="$PROJECT_ID" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo -e "${GREEN}✓ External IP: $EXTERNAL_IP${NC}"

# === Deployment Summary ===
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment সফলভাবে সম্পূর্ণ হয়েছে!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "🌐 Application URL: http://$EXTERNAL_IP:3000"
echo -e "📦 PM2 Status: pm2 list"
echo -e "📋 Logs: pm2 logs hostamar"
echo ""
echo -e "${YELLOW}পরবর্তী ধাপ:${NC}"
echo "1. Nginx reverse proxy setup"
echo "2. SSL certificate (Let's Encrypt)"
echo "3. Cloudflare DNS: A record → $EXTERNAL_IP"
echo ""
echo -e "${GREEN}রিমোট SSH করতে: ${NC}ssh $HOST_ALIAS"
echo -e "${GREEN}VS Code Remote দিয়ে কাজ করতে:${NC} Remote-SSH: Connect to Host → $HOST_ALIAS"
