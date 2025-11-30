# Upload Hostamar Project to GCP VM via Google Cloud Storage
# This avoids IAP stdin errors during file transfer

$BasePath = 'G:\My Drive\Automations'
param(
    [string]$BucketName = "hostamar-deploy",
    [string]$ProjectPath = $BasePath
)

$ErrorActionPreference = "Stop"

Write-Host "Uploading Hostamar Project to GCP VM" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$ARCHIVE_NAME = "hostamar-project-$TIMESTAMP.tar.gz"

# Step 1: Check/Create GCS bucket
Write-Host "Checking GCS bucket..." -ForegroundColor Cyan
$bucketCheck = gcloud storage buckets list --filter="name:$BucketName" --format="value(name)" 2>$null

if ([string]::IsNullOrEmpty($bucketCheck)) {
    Write-Host "  Creating bucket gs://$BucketName..." -ForegroundColor Gray
    gcloud storage buckets create "gs://$BucketName" --location=us-central1 --uniform-bucket-level-access --project=arafat-468807
    Write-Host "  Bucket created" -ForegroundColor Green
} else {
    Write-Host "  Bucket exists" -ForegroundColor Green
}

# Step 2: Create archive using WSL
Write-Host ""
Write-Host "Creating project archive..." -ForegroundColor Cyan

$wslCmd = @'
cd /mnt/g/My\ Drive/Automations && \
tar -czf /tmp/hostamar-project.tar.gz \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.git' \
  --exclude='aiauto_venv' \
  --exclude='*.log' \
  --exclude='.vscode' \
  --exclude='__pycache__' \
    hostamar-platform/ \
    ai-agent/ \
    hybrid-cloud-setup/ \
    scripts/ \
  *.md \
  *.ps1 \
  2>/dev/null && \
echo "OK"
'@

$result = wsl bash -c $wslCmd

if ($result -notmatch "OK") {
    Write-Host "  Archive creation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Archive created" -ForegroundColor Green

# Step 3: Copy to Windows temp
Write-Host ""
Write-Host "Preparing for upload..." -ForegroundColor Cyan
wsl bash -c "cp /tmp/hostamar-project.tar.gz /mnt/c/Users/romel/AppData/Local/Temp/"
$localArchive = "$env:TEMP\hostamar-project.tar.gz"

# Step 4: Upload to GCS
Write-Host "Uploading to Google Cloud Storage..." -ForegroundColor Cyan
Write-Host "  Source: $localArchive" -ForegroundColor Gray
Write-Host "  Destination: gs://$BucketName/$ARCHIVE_NAME" -ForegroundColor Gray

gcloud storage cp $localArchive "gs://$BucketName/$ARCHIVE_NAME"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Upload failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Upload complete" -ForegroundColor Green

# Step 5: Download on VM
Write-Host ""
Write-Host "Downloading to VM..." -ForegroundColor Cyan

$downloadScript = @"
cd ~
echo 'Downloading from GCS...'
gcloud storage cp gs://$BucketName/$ARCHIVE_NAME ./
echo 'Extracting archive...'
tar -xzf $ARCHIVE_NAME
rm $ARCHIVE_NAME
echo 'Done! Project ready at:'
ls -lh ~/hostamar-platform/ ~/ai-agent/ ~/scripts/ 2>/dev/null | head -15
"@

$downloadScript | Out-File -FilePath "$env:TEMP\download.sh" -Encoding ASCII

# Upload download script
Write-Host "  Uploading download script..." -ForegroundColor Gray
Get-Content "$env:TEMP\download.sh" | ssh hostamar-iap 'cat > /tmp/download.sh'

# Execute download script
Write-Host "  Executing download on VM..." -ForegroundColor Gray
ssh hostamar-iap 'bash /tmp/download.sh'

# Cleanup
Write-Host ""
Write-Host "Cleaning up..." -ForegroundColor Cyan
Remove-Item -Path $localArchive -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\download.sh" -Force -ErrorAction SilentlyContinue
wsl bash -c "rm -f /tmp/hostamar-project.tar.gz"

Write-Host ""
Write-Host "Upload Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Project now available on VM at:" -ForegroundColor Cyan
Write-Host "  ~/hostamar-platform/" -ForegroundColor Yellow
Write-Host "  ~/ai-agent/" -ForegroundColor Yellow
Write-Host "  ~/scripts/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. SSH to VM: ssh hostamar-iap" -ForegroundColor Gray
Write-Host "  2. Deploy:    bash ~/scripts/deploy-all-from-vm.sh" -ForegroundColor Gray
Write-Host ""
