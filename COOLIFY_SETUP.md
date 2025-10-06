# Coolify Local DevOps Setup Guide

This guide sets up Coolify as a self-hosted GitHub alternative for local CI/CD, container management, and automated deployments.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available for Coolify
- Port 8000 available (Coolify dashboard)
- Domain or localhost setup

## Step 1: Install Coolify

```powershell
# Create Coolify directory
mkdir C:\coolify
cd C:\coolify

# Download Coolify installation script
curl -fsSL https://cdn.coollabs.io/coolify/install.sh -o install.sh

# For Windows, use Docker directly
docker run --rm -ti -v /var/run/docker.sock:/var/run/docker.sock -v $pwd/coolify:/data/coolify ghcr.io/coollabsio/coolify:latest /usr/bin/coolify-installer
```

### Alternative: Direct Docker Compose Setup

```yaml
# coolify-docker-compose.yml
version: '3.8'
services:
  coolify:
    image: ghcr.io/coollabsio/coolify:latest
    container_name: coolify
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - coolify_data:/data
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - APP_URL=http://localhost:8000
      - DB_CONNECTION=sqlite
      - DB_DATABASE=/data/coolify/database.sqlite

volumes:
  coolify_data:
```

## Step 2: Coolify Configuration

```powershell
# Start Coolify
docker compose -f coolify-docker-compose.yml up -d

# Access dashboard
Start-Process http://localhost:8000

# Follow setup wizard:
# 1. Create admin account
# 2. Configure Git provider (local Git server or existing repos)
# 3. Set up Docker registry
# 4. Configure domains and SSL
```

## Step 3: Project Integration

### Import Fullstack Ecosystem Project

1. **Create New Project** in Coolify dashboard
2. **Connect Git Repository**:
   - Local Git: Use file:// path to your repository
   - Remote Git: Connect to your repository
3. **Configure Build Settings**:
   - Dockerfile path: `./Dockerfile` or Docker Compose
   - Build context: Repository root
   - Environment: Production/Staging

### Environment Variables

```bash
# Coolify environment configuration
APP_NAME=fullstack-ecosystem
APP_ENV=production
COMPOSE_PROJECT_NAME=ecosystem

# Database
POSTGRES_DB=ecosystem_prod
POSTGRES_USER=ecosystem
POSTGRES_PASSWORD=secure_password

# Monitoring
PROMETHEUS_RETENTION=30d
GRAFANA_ADMIN_PASSWORD=secure_admin_pass

# Security
JWT_SECRET=your_jwt_secret_here
API_KEY=your_api_key_here
```

## Step 4: Deployment Configuration

### Coolify Deployment Script

```bash
#!/bin/bash
# deploy.sh - Coolify deployment script

set -e

echo "🚀 Starting Fullstack Ecosystem deployment..."

# Pull latest images
docker compose pull

# Run security scans
echo "🔍 Running security scans..."
./local-container-scan.sh "ecosystem-api:latest,ecosystem-frontend:latest" "./scan-results"

# Check scan results
if [ -f "./scan-results/combined-policy-summary.json" ]; then
    CRITICAL=$(jq '.total_vulnerabilities.critical' ./scan-results/combined-policy-summary.json)
    HIGH=$(jq '.total_vulnerabilities.high' ./scan-results/combined-policy-summary.json)
    
    if [ "$CRITICAL" -gt "0" ] || [ "$HIGH" -gt "5" ]; then
        echo "❌ Security scan failed: $CRITICAL critical, $HIGH high vulnerabilities"
        exit 1
    fi
    echo "✅ Security scan passed"
fi

# Deploy services
echo "📦 Deploying services..."
docker compose up -d --build

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8010/health || exit 1
curl -f http://localhost:5173 || exit 1

# Run smoke tests
echo "🧪 Running smoke tests..."
python scripts/smoke_test.py

echo "✅ Deployment completed successfully!"
```

## Step 5: CI/CD Pipeline Configuration

### Coolify Build Process

```dockerfile
# Dockerfile.coolify - Optimized for Coolify deployment
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim as backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-builder /app/frontend/dist ./static

# Security scanning stage
FROM aquasec/trivy:latest as security-scanner
COPY --from=backend /app /scan-target
RUN trivy fs --format json --output /tmp/scan-results.json /scan-target

# Final runtime
FROM backend as runtime
COPY --from=security-scanner /tmp/scan-results.json /app/security-scan.json
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Coolify Hooks Configuration

```javascript
// coolify-hooks.js - Deployment hooks
module.exports = {
  beforeBuild: async () => {
    console.log('🔍 Pre-build security checks...');
    // Run pre-build validations
  },
  
  afterBuild: async () => {
    console.log('📊 Generating build metrics...');
    // Generate build artifacts
  },
  
  beforeDeploy: async () => {
    console.log('🛡️ Security hardening...');
    // Apply security configurations
  },
  
  afterDeploy: async () => {
    console.log('🎯 Post-deployment validation...');
    // Health checks and smoke tests
  },
  
  onFailure: async (error) => {
    console.error('❌ Deployment failed:', error);
    // Rollback procedures
  }
};
```

## Step 6: Monitoring Integration

### Prometheus Configuration for Coolify

```yaml
# prometheus-coolify.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "coolify_rules.yml"

scrape_configs:
  - job_name: 'coolify'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'ecosystem-api'
    static_configs:
      - targets: ['localhost:8010']
    metrics_path: '/metrics'
    
  - job_name: 'ecosystem-frontend'
    static_configs:
      - targets: ['localhost:5173']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

### Grafana Dashboards for Coolify

```json
{
  "dashboard": {
    "title": "Coolify DevOps Overview",
    "panels": [
      {
        "title": "Deployment Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(coolify_deployments_total{status=\"success\"}[5m]) / rate(coolify_deployments_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "Build Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(coolify_build_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Container Security Scan Results",
        "type": "table",
        "targets": [
          {
            "expr": "coolify_security_vulnerabilities_total"
          }
        ]
      }
    ]
  }
}
```

## Step 7: Security Hardening

### TLS Configuration

```nginx
# nginx-coolify.conf
server {
    listen 443 ssl http2;
    server_name coolify.local;
    
    ssl_certificate /etc/ssl/certs/coolify.crt;
    ssl_certificate_key /etc/ssl/private/coolify.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Secrets Management

```yaml
# coolify-secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: ecosystem-secrets
type: Opaque
data:
  database-url: <base64-encoded-db-url>
  jwt-secret: <base64-encoded-jwt-secret>
  api-key: <base64-encoded-api-key>
```

## Step 8: Automated Backup

```powershell
# backup-coolify.ps1
param(
    [string]$BackupPath = "C:\coolify-backups\$(Get-Date -Format 'yyyy-MM-dd')"
)

Write-Host "🔄 Starting Coolify backup..." -ForegroundColor Green

# Create backup directory
New-Item -ItemType Directory -Path $BackupPath -Force

# Backup Coolify data
docker run --rm -v coolify_data:/data -v "${BackupPath}:/backup" alpine tar czf /backup/coolify-data.tar.gz -C /data .

# Backup database
docker exec coolify-db pg_dump -U postgres ecosystem > "$BackupPath\database.sql"

# Backup configurations
Copy-Item "docker-compose.yml" "$BackupPath\docker-compose.yml"
Copy-Item "coolify-docker-compose.yml" "$BackupPath\coolify-docker-compose.yml"

# Create backup manifest
@{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    backup_path = $BackupPath
    files = @(
        "coolify-data.tar.gz",
        "database.sql",
        "docker-compose.yml",
        "coolify-docker-compose.yml"
    )
} | ConvertTo-Json | Out-File "$BackupPath\manifest.json"

Write-Host "✅ Backup completed: $BackupPath" -ForegroundColor Green
```

## Quick Start Commands

```powershell
# 1. Install and start Coolify
cd C:\coolify
docker compose -f coolify-docker-compose.yml up -d

# 2. Access dashboard
Start-Process http://localhost:8000

# 3. Deploy fullstack ecosystem
cd C:\Users\romel\fullstack-ecosystem
./deploy.sh

# 4. Monitor deployment
Start-Process http://localhost:3000  # Grafana
Start-Process http://localhost:9090  # Prometheus

# 5. Check deployment status
curl http://localhost:8010/health
```

## Benefits of Coolify Setup

✅ **Self-hosted GitHub alternative**
✅ **Integrated CI/CD pipelines**
✅ **Container security scanning**
✅ **Automated deployments**
✅ **Built-in monitoring**
✅ **SSL/TLS management**
✅ **Secrets management**
✅ **Backup automation**

## Next Steps

1. Complete Coolify installation
2. Configure project deployment
3. Set up monitoring integration
4. Implement security hardening
5. Create operational runbooks
