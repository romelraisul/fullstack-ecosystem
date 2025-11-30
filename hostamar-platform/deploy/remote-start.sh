#!/bin/bash
# Start application with PM2 - runs on VM
set -e

cd ~/hostamar-platform

# Install PM2 if needed
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    sudo npm install -g pm2
fi

echo "PM2: $(pm2 --version)"

# Stop existing if running
pm2 delete hostamar 2>/dev/null || true

# Start with PM2
pm2 start npm --name "hostamar" -- start

# Save configuration
pm2 save

# Setup startup script
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME || true

# Show status
pm2 list

echo "Application started!"
