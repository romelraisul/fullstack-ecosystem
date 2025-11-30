#!/bin/bash
# Remote setup script - runs on VM
set -e

cd ~/hostamar-platform

# Install Node.js if needed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node: $(node --version)"
echo "npm: $(npm --version)"

# Install dependencies
echo "Running npm install..."
npm install --production

# Create .env if not exists
if [ ! -f .env ]; then
    cat > .env <<'EOF'
DATABASE_URL="file:./prod.db"
NEXTAUTH_URL="https://hostamar.com"
NEXTAUTH_SECRET="hostamar-nextauth-secret-2025-production-key-12345"
NODE_ENV="production"
PORT=3000
EOF
    echo ".env created"
fi

# Prisma setup
echo "Setting up database..."
npx prisma generate
npx prisma db push --skip-generate

# Build
echo "Building production..."
npm run build

echo "Setup complete!"
