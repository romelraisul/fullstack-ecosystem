#!/bin/bash
set -e

# Configuration
APP_NAME="hostamar-auth-service"
PORT=8000

echo "Deploying $APP_NAME..."

# Build
echo "Building Docker image..."
docker build -t $APP_NAME:latest .

# Stop existing
if [ "$(docker ps -q -f name=$APP_NAME)" ]; then
    echo "Stopping existing container..."
    docker stop $APP_NAME
    docker rm $APP_NAME
fi

# Run
echo "Starting container on port $PORT..."
docker run -d \
    --name $APP_NAME \
    --restart always \
    -p $PORT:8000 \
    -e SECRET_KEY="CHANGE_THIS_IN_PROD" \
    $APP_NAME:latest

echo "Deployment complete! Access Swagger UI at http://<YOUR_IP>:$PORT/docs"
