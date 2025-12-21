#!/bin/bash
set -e
echo "🔧 Fixing Database Configuration..."
cd ~/hostamar-platform

# Backup
cp prisma/schema.prisma prisma/schema.prisma.bak

# Switch Provider
sed -i 's/provider = "sqlite"/provider = "postgresql"/g' prisma/schema.prisma

# Fix Env
# Ensure newline at EOF before appending
sed -i -e '$a\' .env
# Remove any existing DATABASE_URL line
sed -i '/^DATABASE_URL=/d' .env
# Append fresh
echo 'DATABASE_URL="postgresql://hostamar_user:hostamar_secure_2025@localhost:5432/hostamar"' >> .env

echo "✅ Configuration updated."

# Migrate
echo "🔄 Pushing DB schema..."
npx prisma generate
npx prisma db push --accept-data-loss

# Restart
echo "🚀 Restarting App..."
pm2 restart hostamar
echo "✅ Done!"