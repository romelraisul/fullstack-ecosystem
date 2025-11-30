#!/bin/bash
# Complete VM setup script - Run this ON the VM after uploading code

set -e  # Exit on error

echo "=========================================="
echo "  Hostamar Platform VM Setup"
echo "=========================================="

cd ~/hostamar-platform

# Step 1: Install Node.js 20.x
echo ""
echo "Step 1: Installing Node.js 20.x..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "✓ Node.js installed"
else
    echo "✓ Node.js already installed: $(node --version)"
fi

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing npm packages..."
npm install --production
echo "✓ Dependencies installed"

# Step 3: Create .env file
echo ""
echo "Step 3: Creating .env file..."
cat > .env <<'EOF'
DATABASE_URL="file:./prod.db"
NEXTAUTH_URL="https://hostamar.com"
NEXTAUTH_SECRET="hostamar-nextauth-secret-2025-production-key-12345"
NODE_ENV="production"
PORT=3000
EOF
echo "✓ .env file created"

# Step 4: Setup database
echo ""
echo "Step 4: Setting up database..."
npx prisma generate
npx prisma db push --skip-generate
echo "✓ Database ready"

# Step 5: Build application
echo ""
echo "Step 5: Building Next.js application..."
npm run build
echo "✓ Build complete"

# Step 6: Install and configure PM2
echo ""
echo "Step 6: Setting up PM2..."
if ! command -v pm2 &> /dev/null; then
    sudo npm install -g pm2
    echo "✓ PM2 installed"
else
    echo "✓ PM2 already installed"
fi

# Stop any existing process
pm2 delete hostamar 2>/dev/null || true

# Start application
pm2 start npm --name "hostamar" -- start
pm2 save

# Setup PM2 startup
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Application is running on port 3000"
echo ""
echo "Next steps:"
echo "1. Check status: pm2 status"
echo "2. View logs: pm2 logs hostamar"
echo "3. Test locally: curl http://localhost:3000/api/health"
echo ""
