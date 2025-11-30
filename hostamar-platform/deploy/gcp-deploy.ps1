# Hostamar Platform - GCP Mumbai Deployment
# PowerShell Script (Works with Windows gcloud)

Write-Host "=== Hostamar Platform Deployment ===" -ForegroundColor Green
Write-Host ""

# Configuration
$VM_NAME = "hostamar"
$ZONE = "us-central1-a"
$PROJECT_ID = "arafat-468807"
$REMOTE_USER = "romel"
$REMOTE_DIR = "/home/$REMOTE_USER/hostamar-platform"

# Get PROJECT_ID if empty
if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "Getting project ID from gcloud..." -ForegroundColor Yellow
    $PROJECT_ID = gcloud config get-value project 2>$null
    if ([string]::IsNullOrEmpty($PROJECT_ID)) {
        Write-Host "[ERROR] No project configured" -ForegroundColor Red
        Write-Host "Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    }
}

Write-Host "[OK] Project: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Step 1: Configure SSH
Write-Host "Step 1: Configuring SSH..." -ForegroundColor Yellow
gcloud compute config-ssh --project=$PROJECT_ID --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] SSH configuration failed" -ForegroundColor Red
    exit 1
}
$HOST_ALIAS = "$VM_NAME.$ZONE.$PROJECT_ID"
Write-Host "[OK] SSH configured: $HOST_ALIAS" -ForegroundColor Green
Write-Host ""

# Step 2: Get VM IP
Write-Host "Step 2: Getting VM external IP..." -ForegroundColor Yellow
$EXTERNAL_IP = gcloud compute instances describe $VM_NAME `
    --zone=$ZONE `
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
Write-Host "[OK] External IP: $EXTERNAL_IP" -ForegroundColor Green
Write-Host ""

# Step 3: Create remote directory
Write-Host "Step 3: Creating remote directory..." -ForegroundColor Yellow
gcloud compute ssh $VM_NAME --zone=$ZONE --command="mkdir -p $REMOTE_DIR"
Write-Host "[OK] Directory created" -ForegroundColor Green
Write-Host ""

# Step 4: Upload code
Write-Host "Step 4: Uploading code (this will take several minutes)..." -ForegroundColor Yellow
Write-Host "Uploading from: $PSScriptRoot\.." -ForegroundColor Cyan

# Change to project root
Push-Location "$PSScriptRoot\.."

# Use gcloud scp with recursion
gcloud compute scp --recurse `
    --zone=$ZONE `
    --project=$PROJECT_ID `
    . "${VM_NAME}:$REMOTE_DIR"

Pop-Location

Write-Host "[OK] Code uploaded" -ForegroundColor Green
Write-Host ""

# Step 5: Setup environment
Write-Host "Step 5: Setting up environment on VM..." -ForegroundColor Yellow
$setupScript = Get-Content "$PSScriptRoot\remote-setup.sh" -Raw
$setupScript | gcloud compute ssh $VM_NAME --zone=$ZONE --command="bash -s"
Write-Host "[OK] Environment ready" -ForegroundColor Green
Write-Host ""

# Step 6: Start application
Write-Host "Step 6: Starting application with PM2..." -ForegroundColor Yellow
$startScript = Get-Content "$PSScriptRoot\remote-start.sh" -Raw
$startScript | gcloud compute ssh $VM_NAME --zone=$ZONE --command="bash -s"
Write-Host "[OK] Application started" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Application URL: http://$EXTERNAL_IP`:3000" -ForegroundColor Cyan
Write-Host "Health check: http://$EXTERNAL_IP`:3000/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test: curl http://$EXTERNAL_IP`:3000/api/health"
Write-Host "2. SSH: gcloud compute ssh $VM_NAME --zone=$ZONE"
Write-Host "3. Check PM2: pm2 status"
Write-Host "4. View logs: pm2 logs hostamar"
Write-Host "5. Setup Nginx: cd ~/hostamar-platform/deploy; ./nginx-setup.sh"
Write-Host ""
Read-Host -Prompt "Press Enter to exit"
