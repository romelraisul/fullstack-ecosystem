# Simple Coolify Installation Script
param(
    [string]$InstallPath = "C:\coolify",
    [int]$Port = 8000
)

Write-Host "🚀 Installing Coolify..." -ForegroundColor Green

# Create installation directory
New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Set-Location $InstallPath

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create docker-compose.yml
Write-Host "📝 Creating Coolify configuration..." -ForegroundColor Yellow
$composeContent = @"
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
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - APP_URL=http://localhost:$Port
      - DB_CONNECTION=sqlite
      - DB_DATABASE=/data/coolify/database.sqlite

volumes:
  coolify_data:
"@

$composeContent | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

# Create startup script
$startupScript = @"
Write-Host "🚀 Starting Coolify..." -ForegroundColor Green
docker compose up -d
Write-Host "⏳ Waiting for startup..." -ForegroundColor Yellow
Start-Sleep 30
Write-Host "🌐 Access dashboard at: http://localhost:$Port" -ForegroundColor Cyan
Start-Process "http://localhost:$Port"
"@

$startupScript | Out-File -FilePath "start-coolify.ps1" -Encoding UTF8

# Start Coolify
Write-Host "🚀 Starting Coolify..." -ForegroundColor Green
docker compose up -d

Write-Host "⏳ Waiting for Coolify to start..." -ForegroundColor Yellow
Start-Sleep 30

Write-Host "✅ Coolify installation completed!" -ForegroundColor Green
Write-Host "🌐 Dashboard: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "📍 Install path: $InstallPath" -ForegroundColor White

# Open dashboard
Start-Process "http://localhost:$Port"
