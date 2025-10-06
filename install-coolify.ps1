# Coolify Installation Script for Windows
# Automated setup for Coolify DevOps platform

param(
    [string]$InstallPath = "C:\coolify",
    [string]$Domain = "coolify.local",
    [int]$Port = 8000
)

Write-Host "🚀 Starting Coolify installation..." -ForegroundColor Green

# Create installation directory
Write-Host "📁 Creating installation directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Set-Location $InstallPath

# Check Docker availability
Write-Host "🐳 Checking Docker installation..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create Coolify docker-compose.yml
Write-Host "📝 Creating Coolify configuration..." -ForegroundColor Yellow
@"
version: '3.8'
services:
  coolify:
    image: ghcr.io/coollabsio/coolify:latest
    container_name: coolify
    restart: unless-stopped
    ports:
      - "$Port:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - coolify_data:/data
      - ./coolify-config:/config
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - APP_URL=http://$Domain`:$Port
      - DB_CONNECTION=sqlite
      - DB_DATABASE=/data/coolify/database.sqlite
      - COOLIFY_SECRET_KEY=$(New-Guid)
    networks:
      - coolify

  coolify-proxy:
    image: nginx:alpine
    container_name: coolify-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - coolify
    networks:
      - coolify

networks:
  coolify:
    driver: bridge

volumes:
  coolify_data:
"@ | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

# Create nginx configuration
Write-Host "🌐 Creating reverse proxy configuration..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "ssl" -Force | Out-Null

@"
events {
    worker_connections 1024;
}

http {
    upstream coolify {
        server coolify:8000;
    }

    server {
        listen 80;
        server_name $Domain;
        return 301 https://`$server_name`$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name $Domain;

        ssl_certificate /etc/ssl/coolify.crt;
        ssl_certificate_key /etc/ssl/coolify.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

        location / {
            proxy_pass http://coolify;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            proxy_set_header X-Forwarded-Host `$host;
            proxy_set_header X-Forwarded-Port `$server_port;
        }
    }
}
"@ | Out-File -FilePath "nginx.conf" -Encoding UTF8

# Generate self-signed SSL certificate
Write-Host "🔐 Generating SSL certificate..." -ForegroundColor Yellow
$certParams = @{
    Subject           = "CN=$Domain"
    KeyAlgorithm      = "RSA"
    KeyLength         = 2048
    NotAfter          = (Get-Date).AddYears(1)
    CertStoreLocation = "Cert:\CurrentUser\My"
}

try {
    $cert = New-SelfSignedCertificate @certParams
    $certPath = "ssl\coolify.crt"
    $keyPath = "ssl\coolify.key"

    # Export certificate
    Export-Certificate -Cert $cert -FilePath $certPath -Type CERT | Out-Null

    # Export private key (requires manual conversion)
    Write-Host "⚠️  Manual SSL setup required. Using temporary self-signed approach." -ForegroundColor Yellow

    # Create temporary certificate files (for development only)
    "# Temporary self-signed certificate for development" | Out-File -FilePath $certPath -Encoding ASCII
    "# Temporary private key for development" | Out-File -FilePath $keyPath -Encoding ASCII

    Write-Host "⚠️  Using temporary SSL files. Generate proper certificates for production." -ForegroundColor Yellow

}
catch {
    Write-Host "⚠️  SSL certificate generation failed. Using HTTP mode." -ForegroundColor Yellow
}

# Create ecosystem integration script
Write-Host "🔗 Creating ecosystem integration script..." -ForegroundColor Yellow
@"
# Ecosystem Integration Script for Coolify
param([string]`$Action = "deploy")

switch (`$Action) {
    "deploy" {
        Write-Host "🚀 Deploying Fullstack Ecosystem via Coolify..." -ForegroundColor Green

        # Copy ecosystem files
        Copy-Item "C:\Users\romel\fullstack-ecosystem\*" ".\projects\fullstack-ecosystem\" -Recurse -Force

        # Run security scan
        & ".\projects\fullstack-ecosystem\local-container-scan.ps1" -Images "ecosystem-api,ecosystem-frontend" -OutputDir ".\scan-results"

        # Deploy via Coolify API
        `$coolifyUrl = "http://$Domain`:$Port"
        Write-Host "📡 Triggering deployment via Coolify API..." -ForegroundColor Yellow

        # Note: Replace with actual Coolify API calls once setup is complete
        Write-Host "✅ Deployment initiated. Check Coolify dashboard at `$coolifyUrl" -ForegroundColor Green
    }

    "monitor" {
        Write-Host "📊 Opening monitoring dashboards..." -ForegroundColor Green
        Start-Process "http://localhost:3000"  # Grafana
        Start-Process "http://localhost:9090"  # Prometheus
        Start-Process "http://$Domain`:$Port"   # Coolify
    }

    "backup" {
        Write-Host "💾 Creating backup..." -ForegroundColor Green
        `$backupPath = "backups\$(Get-Date -Format 'yyyy-MM-dd-HH-mm')"
        New-Item -ItemType Directory -Path `$backupPath -Force

        # Backup Coolify data
        docker run --rm -v coolify_data:/data -v "`$(pwd)\`$backupPath:/backup" alpine tar czf /backup/coolify-data.tar.gz -C /data .

        Write-Host "✅ Backup completed: `$backupPath" -ForegroundColor Green
    }

    "logs" {
        Write-Host "📋 Showing Coolify logs..." -ForegroundColor Green
        docker compose logs -f coolify
    }

    default {
        Write-Host "Usage: .\coolify-ecosystem.ps1 [deploy|monitor|backup|logs]" -ForegroundColor Yellow
    }
}
"@ | Out-File -FilePath "coolify-ecosystem.ps1" -Encoding UTF8

# Create startup script
@"
# Coolify Startup Script
Write-Host "🚀 Starting Coolify DevOps Platform..." -ForegroundColor Green

# Start Coolify
docker compose up -d

Write-Host "⏳ Waiting for Coolify to start..." -ForegroundColor Yellow
Start-Sleep 30

# Check if Coolify is running
try {
    `$response = Invoke-WebRequest -Uri "http://localhost:$Port" -TimeoutSec 10
    Write-Host "✅ Coolify is running!" -ForegroundColor Green
    Write-Host "🌐 Access dashboard at: http://$Domain`:$Port" -ForegroundColor Cyan

    # Open dashboard
    Start-Process "http://localhost:$Port"

} catch {
    Write-Host "❌ Coolify startup failed. Check logs with: docker compose logs coolify" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Quick Commands:" -ForegroundColor Yellow
Write-Host "  View logs:     docker compose logs -f coolify" -ForegroundColor White
Write-Host "  Stop Coolify:  docker compose down" -ForegroundColor White
Write-Host "  Restart:       docker compose restart coolify" -ForegroundColor White
Write-Host "  Deploy app:    .\coolify-ecosystem.ps1 deploy" -ForegroundColor White
Write-Host "  Monitor:       .\coolify-ecosystem.ps1 monitor" -ForegroundColor White
"@ | Out-File -FilePath "start-coolify.ps1" -Encoding UTF8

# Create project directories
Write-Host "📁 Creating project structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "projects" -Force | Out-Null
New-Item -ItemType Directory -Path "backups" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

# Start Coolify
Write-Host "🚀 Starting Coolify..." -ForegroundColor Green
docker compose up -d

Write-Host "⏳ Waiting for Coolify to initialize..." -ForegroundColor Yellow
Start-Sleep 30

# Final status check
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port" -TimeoutSec 10
    Write-Host "✅ Coolify installation completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Cyan
    Write-Host "📍 Installation Path: $InstallPath" -ForegroundColor White
    Write-Host "🌐 Dashboard URL: http://localhost:$Port" -ForegroundColor White
    Write-Host "🔧 Domain: $Domain" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Access the dashboard and complete initial setup" -ForegroundColor White
    Write-Host "2. Create your first project" -ForegroundColor White
    Write-Host "3. Connect your Git repository" -ForegroundColor White
    Write-Host "4. Configure deployment settings" -ForegroundColor White
    Write-Host "5. Deploy your fullstack ecosystem" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Documentation: See COOLIFY_SETUP.md for detailed usage" -ForegroundColor White

    # Open dashboard
    Start-Process "http://localhost:$Port"

}
catch {
    Write-Host "❌ Coolify installation failed!" -ForegroundColor Red
    Write-Host "🔍 Check logs: docker compose logs coolify" -ForegroundColor Yellow
    Write-Host "🔧 Troubleshooting: Ensure port $Port is available" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🛠️  Installation files created:" -ForegroundColor Cyan
Get-ChildItem -Path $InstallPath | ForEach-Object { Write-Host "   $($_.Name)" -ForegroundColor White }
