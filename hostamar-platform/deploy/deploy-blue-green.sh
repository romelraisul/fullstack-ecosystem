#!/bin/bash
set -e

# ==========================================
# Hostamar Blue-Green Deployment Engine
# Zero Downtime Strategy
# ==========================================

APP_NAME="hostamar-platform"
IMAGE_NAME="hostamar-platform:latest"
BLUE_PORT=3001
GREEN_PORT=3002
GATEWAY_PORT=8080
NETWORK="hostamar-net"

# Ensure Docker network exists
docker network create $NETWORK 2>/dev/null || true

echo "[1/6] Building new version..."
docker build -t $IMAGE_NAME .

# Determine Active Environment
if docker ps --format '{{.Names}}' | grep -q "${APP_NAME}-blue"; then
    CURRENT="blue"
    TARGET="green"
    TARGET_PORT=$GREEN_PORT
else
    CURRENT="green"
    TARGET="blue"
    TARGET_PORT=$BLUE_PORT
fi

echo "[2/6] Detected Active: $CURRENT. Deploying to: $TARGET"

# Cleanup Target
docker rm -f ${APP_NAME}-${TARGET} 2>/dev/null || true

# Run Target Container
echo "[3/6] Starting $TARGET container..."
# Note: Ensure DATABASE_URL is set in environment or .env file
docker run -d \
    --name ${APP_NAME}-${TARGET} \
    --network $NETWORK \
    -p $TARGET_PORT:3000 \
    --restart always \
    --env-file .env \
    $IMAGE_NAME

# Health Check
echo "[4/6] Performing Health Check on $TARGET..."
HEALTHY=false
for i in {1..30}; do
    if curl -s http://localhost:$TARGET_PORT > /dev/null; then
        echo "✓ Health check passed!"
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$HEALTHY" = false ]; then
    echo "❌ Health check failed. Aborting deployment."
    docker stop ${APP_NAME}-${TARGET}
    exit 1
fi

# Switch Traffic via Local Nginx Gateway
echo "[5/6] Switching Traffic to $TARGET..."

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
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
EOF

if docker ps --format '{{.Names}}' | grep -q "hostamar-gateway"; then
    docker cp nginx-gateway.conf hostamar-gateway:/etc/nginx/nginx.conf
    docker exec hostamar-gateway nginx -s reload
else
    docker run -d \
        --name hostamar-gateway \
        --network $NETWORK \
        -p $GATEWAY_PORT:80 \
        --restart always \
        -v $(pwd)/nginx-gateway.conf:/etc/nginx/nginx.conf \
        nginx:alpine
fi

# Finalize
echo "[6/6] Deployment Complete. $TARGET is now LIVE."
echo "Previous version ($CURRENT) is kept running for quick rollback."
echo "To Rollback: Run './rollback.sh'"
