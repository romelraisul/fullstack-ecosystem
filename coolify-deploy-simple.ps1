# Simple Coolify Deployment Script
param(
    [string]$CoolifyPath = "C:\coolify",
    [string]$Action = "deploy"
)

Write-Host "🚀 Starting Coolify Deployment" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Step 1: Create directories
Write-Host "📁 Creating directory structure..." -ForegroundColor Cyan
$directories = @(
    $CoolifyPath,
    "$CoolifyPath\ssl",
    "$CoolifyPath\data",
    "$CoolifyPath\logs",
    "$CoolifyPath\scripts"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor White
    }
}

# Step 2: Copy scripts
Write-Host "📄 Copying automation scripts..." -ForegroundColor Cyan
$scriptFiles = @(
    "install-coolify.ps1",
    "security-hardening.ps1",
    "comprehensive-monitoring.ps1"
)

foreach ($script in $scriptFiles) {
    if (Test-Path ".\$script") {
        Copy-Item ".\$script" "$CoolifyPath\scripts\$script" -Force
        Write-Host "   Copied: $script" -ForegroundColor White
    }
}

# Step 3: Run installation
if ($Action -eq "deploy" -or $Action -eq "install") {
    Write-Host "🐳 Installing Coolify..." -ForegroundColor Cyan

    Push-Location $CoolifyPath

    try {
        if (Test-Path ".\scripts\install-coolify.ps1") {
            & ".\scripts\install-coolify.ps1" -CoolifyPath $CoolifyPath
            Write-Host "✅ Coolify installation completed!" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Install script not found, running basic setup..." -ForegroundColor Yellow

            # Basic Docker Compose setup
            $dockerCompose = @'
version: '3.8'

services:
  coolify:
    image: coollabsio/coolify:latest
    container_name: coolify
    restart: unless-stopped
    ports:
      - "8000:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - coolify_data:/data
    environment:
      - APP_NAME=Coolify
      - APP_ENV=production
      - APP_DEBUG=false

volumes:
  coolify_data:
'@
            $dockerCompose | Out-File "docker-compose.yml" -Encoding UTF8

            # Start services
            docker-compose up -d
        }
    } catch {
        Write-Host "❌ Installation error: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

# Step 4: Apply security (if available)
if (Test-Path "$CoolifyPath\scripts\security-hardening.ps1") {
    Write-Host "🔒 Applying security hardening..." -ForegroundColor Cyan
    try {
        & "$CoolifyPath\scripts\security-hardening.ps1" -CoolifyPath $CoolifyPath
        Write-Host "✅ Security hardening completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Security hardening failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 5: Setup monitoring (if available)
if (Test-Path "$CoolifyPath\scripts\comprehensive-monitoring.ps1") {
    Write-Host "📊 Setting up monitoring..." -ForegroundColor Cyan
    try {
        & "$CoolifyPath\scripts\comprehensive-monitoring.ps1" -CoolifyPath $CoolifyPath
        Write-Host "✅ Monitoring setup completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Monitoring setup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 6: Test deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Cyan
try {
    Start-Sleep -Seconds 10  # Wait for services to start

    # Check Docker containers
    $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -match "coolify" }
    if ($containers) {
        Write-Host "✅ Coolify containers are running" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No Coolify containers found" -ForegroundColor Yellow
    }

    # Test endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 10 -UseBasicParsing
        Write-Host "✅ Coolify web interface is accessible" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Coolify web interface not responding yet" -ForegroundColor Yellow
    }

} catch {
    Write-Host "⚠️ Testing failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final summary
Write-Host ""
Write-Host "🎉 Coolify Deployment Summary" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host "Installation Path: $CoolifyPath" -ForegroundColor White
Write-Host "Web Interface: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Visit http://localhost:8000 to access Coolify" -ForegroundColor White
Write-Host "2. Complete the initial setup wizard" -ForegroundColor White
Write-Host "3. Configure your first project" -ForegroundColor White
Write-Host ""
Write-Host "✅ Deployment completed!" -ForegroundColor Green
