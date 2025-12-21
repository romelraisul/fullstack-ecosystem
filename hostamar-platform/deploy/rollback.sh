#!/bin/bash
set -e

# ==========================================
# Hostamar Rollback Engine
# ==========================================

APP_NAME="hostamar-platform"
GATEWAY_PORT=8080

echo "Initiating Rollback..."

if docker ps --format '{{.Names}}' | grep -q "${APP_NAME}-blue"; then
    BLUE_RUNNING=true
else
    BLUE_RUNNING=false
fi

if docker ps --format '{{.Names}}' | grep -q "${APP_NAME}-green"; then
    GREEN_RUNNING=true
else
    GREEN_RUNNING=false
fi

# Determine current live by checking nginx config (simplified: assume we want to flip)
# Better: User tells us which one to restore, or we infer the one that was just stopped/inactive
# For simplicity: If Blue is live (in config), we switch to Green IF it's running.

# Check Nginx Config content inside container
CURRENT_CONFIG=$(docker exec hostamar-gateway cat /etc/nginx/nginx.conf)

if [[ "$CURRENT_CONFIG" == *"${APP_NAME}-blue"* ]]; then
    CURRENT="blue"
    TARGET="green"
elif [[ "$CURRENT_CONFIG" == *"${APP_NAME}-green"* ]]; then
    CURRENT="green"
    TARGET="blue"
else
    echo "Unknown state."
    exit 1
fi

echo "Current Live: $CURRENT. Attempting rollback to: $TARGET"

if [ "$TARGET" == "blue" ] && [ "$BLUE_RUNNING" == "false" ]; then
    echo "❌ Cannot rollback: Blue container is not running."
    exit 1
fi

if [ "$TARGET" == "green" ] && [ "$GREEN_RUNNING" == "false" ]; then
    echo "❌ Cannot rollback: Green container is not running."
    exit 1
fi

# Switch Nginx
cat <<EOF > nginx-gateway.conf
events {}
http {
    upstream backend {
        server ${APP_NAME}-${TARGET}:3000;
    }
    server {
        listen 80;
        server_name _;
        location / {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
    }
}
EOF

docker cp nginx-gateway.conf hostamar-gateway:/etc/nginx/nginx.conf
docker exec hostamar-gateway nginx -s reload

echo "✅ Rollback Successful. $TARGET is now LIVE."
