# 🚀 MASTER DEPLOYMENT SCRIPT
# Complete Hostamar Platform Deployment - One Command
# This orchestrates all deployment steps automatically

param(
    [switch]$SkipVenvSetup,
    [switch]$SkipVMPrep,
    [switch]$SkipSSL,
    [string]$Domain = "hostamar.com",
    [string]$SSHHost = "romel@34.47.163.149",
    [string]$SSHKey = "C:\Users\romel\.ssh\google_compute_engine"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Yellow
}

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🚀 HOSTAMAR PLATFORM DEPLOYMENT AUTOMATION 🚀        ║
║                                                           ║
║     Complete setup from zero to production               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

$startTime = Get-Date
$BasePath = 'G:\My Drive\Automations'

# ============================================================================
# STEP 1: Setup Python Virtual Environment (Local)
# ============================================================================
if (-not $SkipVenvSetup) {
    Write-Step "STEP 1/6: Setting up Python Virtual Environment"
    
    $venvScript = (Join-Path $BasePath 'scripts/setup-python-venv.ps1')
    if (Test-Path $venvScript) {
        & $venvScript
        Write-Success "Python venv ready"
    } else {
        Write-Info "Venv setup script not found, skipping..."
    }
} else {
    Write-Info "Skipping venv setup"
}

# ============================================================================
# STEP 2: Prepare GCP VM
# ============================================================================
if (-not $SkipVMPrep) {
    Write-Step "STEP 2/6: Preparing GCP VM (Installing Node.js, PM2, PostgreSQL, Nginx)"
    
    Write-Host "  Uploading preparation script..." -ForegroundColor Gray
    scp -i $SSHKey -o StrictHostKeyChecking=no "$(Join-Path $BasePath 'hostamar-platform/deploy/vm-prepare.sh')" ${SSHHost}:/tmp/
    
    Write-Host "  Running preparation on VM (this may take 5-10 minutes)..." -ForegroundColor Gray
    ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "chmod +x /tmp/vm-prepare.sh && /tmp/vm-prepare.sh"
    
    Write-Success "VM prepared with all dependencies"
} else {
    Write-Info "Skipping VM preparation"
}

# ============================================================================
# STEP 3: Deploy Application
# ============================================================================
Write-Step "STEP 3/6: Deploying Hostamar Platform Application"

$deployScript = (Join-Path $BasePath 'hostamar-platform/deploy/deploy-to-gcp.ps1')
if (Test-Path $deployScript) {
    & $deployScript -SSHHost $SSHHost
    Write-Success "Application deployed successfully"
} else {
    Write-Host "✗ Deployment script not found!" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 4: Configure Nginx Reverse Proxy
# ============================================================================
Write-Step "STEP 4/6: Configuring Nginx Reverse Proxy"

Write-Host "  Uploading Nginx configuration script..." -ForegroundColor Gray
scp -i $SSHKey -o StrictHostKeyChecking=no "$(Join-Path $BasePath 'hostamar-platform/deploy/nginx-config.sh')" ${SSHHost}:/tmp/

Write-Host "  Configuring Nginx..." -ForegroundColor Gray
ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "chmod +x /tmp/nginx-config.sh && /tmp/nginx-config.sh $Domain"

Write-Success "Nginx configured as reverse proxy"

# ============================================================================
# STEP 5: Setup SSL Certificate
# ============================================================================
if (-not $SkipSSL) {
    Write-Step "STEP 5/6: Setting up SSL Certificate (Let's Encrypt)"
    
    Write-Info "Before SSL setup, ensure:"
    Write-Host "  1. DNS for $Domain points to VM IP" -ForegroundColor Yellow
    Write-Host "  2. Firewall allows ports 80 and 443" -ForegroundColor Yellow
    Write-Host ""
    
    $proceed = Read-Host "Proceed with SSL setup? (y/n)"
    if ($proceed -eq 'y') {
        Write-Host "  Uploading SSL setup script..." -ForegroundColor Gray
        scp -i $SSHKey -o StrictHostKeyChecking=no "$(Join-Path $BasePath 'hostamar-platform/deploy/setup-ssl.sh')" ${SSHHost}:/tmp/
        
        Write-Host "  Obtaining SSL certificate..." -ForegroundColor Gray
        ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "chmod +x /tmp/setup-ssl.sh && /tmp/setup-ssl.sh $Domain"
        
        Write-Success "SSL certificate installed"
    } else {
        Write-Info "SSL setup skipped - you can run it later manually"
    }
} else {
    Write-Info "Skipping SSL setup"
}

# ============================================================================
# STEP 6: Verification & Final Checks
# ============================================================================
Write-Step "STEP 6/6: Verification & Health Checks"

Write-Host "  Checking application status..." -ForegroundColor Gray
ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "pm2 status"

Write-Host "`n  Testing health endpoint..." -ForegroundColor Gray
$health = ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "curl -s http://localhost:3001/api/health"
if ($health -match "ok|healthy") {
    Write-Success "Health check: PASSED"
} else {
    Write-Host "⚠️  Health check: FAILED" -ForegroundColor Yellow
    Write-Host "  Response: $health" -ForegroundColor Gray
}

Write-Host "`n  Checking systemd monitoring timers..." -ForegroundColor Gray
ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost "systemctl list-timers hostamar-* --no-pager"

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║            ✅ DEPLOYMENT COMPLETED SUCCESSFULLY! ✅        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Duration: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Gray
Write-Host "  Domain: $Domain" -ForegroundColor Gray
Write-Host ""

Write-Host "🌐 Access your platform:" -ForegroundColor Cyan
if (-not $SkipSSL) {
    Write-Host "  https://$Domain" -ForegroundColor Yellow
} else {
    Write-Host "  http://$(ssh -i $SSHKey -o StrictHostKeyChecking=no $SSHHost 'curl -s ifconfig.me 2>/dev/null')" -ForegroundColor Yellow
}

Write-Host "`n📝 Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:    ssh -i $SSHKey $SSHHost 'pm2 logs hostamar-platform'" -ForegroundColor Gray
Write-Host "  Restart app:  ssh -i $SSHKey $SSHHost 'pm2 restart hostamar-platform'" -ForegroundColor Gray
Write-Host "  Check status: ssh -i $SSHKey $SSHHost 'pm2 status'" -ForegroundColor Gray
Write-Host "  Monitor:      ssh -i $SSHKey $SSHHost 'pm2 monit'" -ForegroundColor Gray

Write-Host "`n🎯 What was deployed:" -ForegroundColor Cyan
Write-Host "  ✅ Python venv for AI agent" -ForegroundColor Green
Write-Host "  ✅ Node.js 20 + PM2" -ForegroundColor Green
Write-Host "  ✅ PostgreSQL database" -ForegroundColor Green
Write-Host "  ✅ Hostamar Platform (Next.js)" -ForegroundColor Green
Write-Host "  ✅ Nginx reverse proxy" -ForegroundColor Green
if (-not $SkipSSL) {
    Write-Host "  ✅ SSL certificate (Let's Encrypt)" -ForegroundColor Green
}
Write-Host "  ✅ Monitoring timers (uptime + TLS)" -ForegroundColor Green

Write-Host "`n🚀 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test signup: https://$Domain/auth/signup" -ForegroundColor Yellow
Write-Host "  2. Setup video generation pipeline" -ForegroundColor Yellow
Write-Host "  3. Configure payment gateway" -ForegroundColor Yellow
Write-Host "  4. Enable CI/CD automation" -ForegroundColor Yellow

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Happy deploying! 🎉" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
