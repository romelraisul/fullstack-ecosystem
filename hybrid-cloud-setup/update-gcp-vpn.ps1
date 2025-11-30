# Update GCP WireGuard configuration from Windows
# Run this in PowerShell

Write-Host "Updating GCP WireGuard server..." -ForegroundColor Cyan

# Set project
gcloud config set project arafat-468807

# SSH and update WireGuard
gcloud compute ssh migrated-vm-asia `
    --zone=asia-south1-b `
    --command="sudo wg set wg0 peer XTAAjnYgjnpLjpV9ZJ3a2Ke0n8o0jP4KYwfH1bXShHA= allowed-ips 10.10.0.2/32 && sudo wg-quick save wg0 && echo 'Updated successfully' && sudo wg show"

Write-Host "`nTesting VPN connectivity..." -ForegroundColor Cyan
Test-Connection -ComputerName 10.10.0.1 -Count 4

Write-Host "`nDone! If ping works, VPN is active." -ForegroundColor Green
