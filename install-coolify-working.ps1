# Working Coolify Installation Script
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

# Create docker-compose.yml file content
Write-Host "📝 Creating Coolify configuration..." -ForegroundColor Yellow

# Use array of strings instead of here-string to avoid parsing issues
$composeLines = @(
    "version: '3.8'",
    "services:",
    "  coolify:",
    "    image: ghcr.io/coollabsio/coolify:latest",
    "    container_name: coolify",
    "    restart: unless-stopped",
    "    ports:",
    "      - `"$Port`:8000`"",
    "    volumes:",
    "      - /var/run/docker.sock:/var/run/docker.sock",
    "      - coolify_data:/data",
    "    environment:",
    "      - APP_ENV=production",
    "      - APP_DEBUG=false",
    "      - APP_URL=http://localhost:$Port",
    "      - DB_CONNECTION=sqlite",
    "      - DB_DATABASE=/data/coolify/database.sqlite",
    "",
    "volumes:",
    "  coolify_data:"
)

$composeLines | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

# Create startup script
$startupLines = @(
    "Write-Host `"🚀 Starting Coolify...`" -ForegroundColor Green",
    "docker compose up -d",
    "Write-Host `"⏳ Waiting for startup...`" -ForegroundColor Yellow",
    "Start-Sleep 30",
    "Write-Host `"🌐 Access dashboard at: http://localhost:$Port`" -ForegroundColor Cyan",
    "Start-Process `"http://localhost:$Port`""
)

$startupLines | Out-File -FilePath "start-coolify.ps1" -Encoding UTF8

# Create ecosystem integration script
$ecosystemLines = @(
    "# Ecosystem Integration for Coolify",
    "param([string]`$Action = `"status`")",
    "",
    "switch (`$Action) {",
    "    `"deploy`" {",
    "        Write-Host `"🚀 Deploying ecosystem...`" -ForegroundColor Green",
    "        # Copy project files and deploy",
    "        Copy-Item `"C:\Users\romel\fullstack-ecosystem\*`" `".\projects\fullstack-ecosystem\`" -Recurse -Force",
    "        Write-Host `"✅ Project copied to Coolify`" -ForegroundColor Green",
    "    }",
    "    `"scan`" {",
    "        Write-Host `"🔍 Running security scan...`" -ForegroundColor Yellow",
    "        & `"C:\Users\romel\fullstack-ecosystem\local-container-scan.ps1`" -Images `"alpine:latest`" -OutputDir `".\scan-results`"",
    "    }",
    "    `"monitor`" {",
    "        Write-Host `"📊 Opening monitoring...`" -ForegroundColor Green",
    "        Start-Process `"http://localhost:3000`"",
    "        Start-Process `"http://localhost:9090`"",
    "        Start-Process `"http://localhost:$Port`"",
    "    }",
    "    default {",
    "        Write-Host `"Usage: .\ecosystem.ps1 [deploy|scan|monitor]`" -ForegroundColor Yellow",
    "        Write-Host `"Coolify dashboard: http://localhost:$Port`" -ForegroundColor Cyan",
    "    }",
    "}"
)

$ecosystemLines | Out-File -FilePath "ecosystem.ps1" -Encoding UTF8

# Create project directory
New-Item -ItemType Directory -Path "projects" -Force | Out-Null

Write-Host "📦 Pulling Coolify image..." -ForegroundColor Yellow
docker pull ghcr.io/coollabsio/coolify:latest

# Start Coolify
Write-Host "🚀 Starting Coolify..." -ForegroundColor Green
docker compose up -d

Write-Host "⏳ Waiting for Coolify to start..." -ForegroundColor Yellow
Start-Sleep 45

# Check if Coolify is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Coolify is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Coolify may still be starting. Check with: docker compose logs coolify" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Coolify installation completed!" -ForegroundColor Green
Write-Host "📍 Installation path: $InstallPath" -ForegroundColor White
Write-Host "🌐 Dashboard URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Quick commands:" -ForegroundColor Yellow
Write-Host "  .\start-coolify.ps1     - Start Coolify" -ForegroundColor White
Write-Host "  .\ecosystem.ps1 deploy  - Deploy ecosystem" -ForegroundColor White
Write-Host "  .\ecosystem.ps1 scan    - Run security scan" -ForegroundColor White
Write-Host "  .\ecosystem.ps1 monitor - Open monitoring" -ForegroundColor White
Write-Host ""
Write-Host "📖 View logs: docker compose logs -f coolify" -ForegroundColor White

# Open dashboard
Start-Process "http://localhost:$Port"
