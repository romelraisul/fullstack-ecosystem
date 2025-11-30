# Hostamar Platform Deployment Script
# Deploy Next.js app to GCP VM via SSH

param(
    [string]$SSHHost = "hostamar-iap",
    [string]$RemotePath = "/var/www/hostamar",
    [switch]$SkipBuild,
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Hostamar Platform Deployment" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$BasePath = 'G:\My Drive\Automations'
$LOCAL_PATH = (Join-Path $BasePath 'hostamar-platform')
$WSL_LOCAL_PATH = "/mnt/g/My\\ Drive/Automations/hostamar-platform/"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"

# Check if SSH config exists
if (-not (Test-Path "$HOME\.ssh\config")) {
    Write-Host "✗ SSH config not found!" -ForegroundColor Red
    exit 1
}

# Step 1: Build locally
if (-not $SkipBuild) {
    Write-Host "🔨 Building Next.js application..." -ForegroundColor Cyan
    Push-Location $LOCAL_PATH
    
    # Install dependencies
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    npm install --silent
    
    # Build production
    Write-Host "  Building for production..." -ForegroundColor Gray
    $env:NODE_ENV = "production"
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ Build complete" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "⏭ Skipping build (using existing)" -ForegroundColor Yellow
}

# Step 2: Create .env.production
Write-Host "`n🔐 Creating production environment file..." -ForegroundColor Cyan
$envContent = @"
# Production Environment Variables
NODE_ENV=production
DATABASE_URL="postgresql://hostamar_user:hostamar_secure_2025@localhost:5432/hostamar?schema=public"
NEXTAUTH_SECRET="$(([char[]]([char]33..[char]126) | Get-Random -Count 32) -join '')"
NEXTAUTH_URL="https://hostamar.com"
"@

Set-Content -Path "$LOCAL_PATH\.env.production" -Value $envContent
Write-Host "✓ Environment file created" -ForegroundColor Green

# Step 3: Backup existing deployment (if not skipped)
if (-not $SkipBackup) {
    Write-Host "`n💾 Creating backup of existing deployment..." -ForegroundColor Cyan
    $backupCmd = "if [ -d $RemotePath ]; then sudo tar -czf /tmp/hostamar-backup-$TIMESTAMP.tar.gz -C $RemotePath . && echo 'Backup created'; else echo 'No existing deployment'; fi"
    ssh $SSHHost $backupCmd
    Write-Host "✓ Backup complete" -ForegroundColor Green
}

# Step 4: Sync files to VM
Write-Host "`n📤 Syncing files to GCP VM..." -ForegroundColor Cyan
Write-Host "  Source: $LOCAL_PATH" -ForegroundColor Gray
Write-Host "  Destination: ${SSHHost}:${RemotePath}" -ForegroundColor Gray

# Use WSL rsync for better compatibility
$rsyncCmd = @"
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.git' \
    --exclude '.env.local' \
    --exclude '.vscode' \
    --exclude 'eval/outputs' \
    "$WSL_LOCAL_PATH" \
    ${SSHHost}:${RemotePath}/
"@

wsl bash -c $rsyncCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ File sync failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Files synced successfully" -ForegroundColor Green

# Step 5: Install dependencies on VM
Write-Host "`n📦 Installing dependencies on VM..." -ForegroundColor Cyan
ssh $SSHHost "cd $RemotePath && npm install --production --silent"
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 6: Run database migrations
Write-Host "`n🗄️  Running database migrations..." -ForegroundColor Cyan
ssh $SSHHost "cd $RemotePath && npx prisma generate && npx prisma db push --skip-generate"
Write-Host "✓ Database migrated" -ForegroundColor Green

# Step 7: Build on VM (using production .env)
Write-Host "`n🔨 Building on VM..." -ForegroundColor Cyan
ssh $SSHHost "cd $RemotePath && npm run build"
Write-Host "✓ Build complete on VM" -ForegroundColor Green

# Step 8: Restart PM2
Write-Host "`n🔄 Restarting application with PM2..." -ForegroundColor Cyan

$pm2Config = @"
module.exports = {
  apps: [{
    name: 'hostamar-platform',
    script: 'npm',
    args: 'start',
    cwd: '$RemotePath',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 3001
    }
  }]
}
"@

# Create PM2 config
$pm2Config | ssh $SSHHost "cat > $RemotePath/ecosystem.config.js"

# Start/restart with PM2
ssh $SSHHost "cd $RemotePath && pm2 delete hostamar-platform 2>/dev/null || true && pm2 start ecosystem.config.js && pm2 save"
Write-Host "✓ Application started with PM2" -ForegroundColor Green

# Step 9: Verify deployment
Write-Host "`n✅ Verifying deployment..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

$healthCheck = ssh $SSHHost "curl -s http://localhost:3001/api/health || echo 'FAIL'"
if ($healthCheck -match "ok|healthy") {
    Write-Host "✓ Health check passed!" -ForegroundColor Green
} else {
    Write-Host "⚠ Health check failed - check logs" -ForegroundColor Yellow
}

# Show PM2 status
Write-Host "`n📊 Application Status:" -ForegroundColor Cyan
ssh $SSHHost "pm2 status"

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Configure Nginx reverse proxy (run deploy-nginx.sh)" -ForegroundColor Yellow
Write-Host "  2. Setup SSL certificate (run setup-ssl.sh)" -ForegroundColor Yellow
Write-Host "  3. Test: ssh $SSHHost 'curl http://localhost:3001'" -ForegroundColor Yellow
Write-Host "`nView logs:" -ForegroundColor Cyan
Write-Host "  ssh $SSHHost 'pm2 logs hostamar-platform'" -ForegroundColor Yellow
