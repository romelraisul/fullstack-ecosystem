#!/bin/bash
set -e
cd ~

if [ -f hostamar-source.tar.gz ]; then
    echo "📦 Extracting new source..."
    tar xzf hostamar-source.tar.gz
fi

cd ~/hostamar-platform

echo "🔧 Writing clean .env..."
cat > .env <<EOF
# Production Env
DATABASE_URL="postgresql://hostamar_user:hostamar_secure_2025@localhost:5432/hostamar"
NEXTAUTH_URL="https://hostamar.com"
NEXTAUTH_SECRET="qkcqZGNeCrQGLnIkl5Lc+yIbi+qVQwFRCo76hswGRjM="
# Add other keys as needed
EOF

echo "🔧 Fixing Schema Provider..."
sudo sed -i 's/provider = "sqlite"/provider = "postgresql"/g' prisma/schema.prisma

echo "📦 Installing AI Dependencies..."
# Force install of the missing packages
npm install @google/generative-ai @aws-sdk/client-s3 --save --legacy-peer-deps

echo "🔄 Generating Client..."
npx prisma generate

echo "🗄️  Pushing DB Schema..."
npx prisma db push --accept-data-loss

echo "🏗️  Building App..."
npm run build

echo "🚀 Launching..."
pm2 start ecosystem.config.js --env production
pm2 save

echo "✅ Mission Accomplished."