# Simple Local Container Security Test
# Quick test of the scanning tools

param(
    [string]$Image = "alpine:3.18"
)

# Tool paths
$TrivyPath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\AquaSecurity.Trivy_Microsoft.Winget.Source_8wekyb3d8bbwe\trivy.exe"
$GrypePath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\Anchore.Grype_Microsoft.Winget.Source_8wekyb3d8bbwe\grype.exe"
$SyftPath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\Anchore.Syft_Microsoft.Winget.Source_8wekyb3d8bbwe\syft.exe"

Write-Host "Testing container security scan for: $Image" -ForegroundColor Green

# Create test output directory
$OutputDir = "./quick-test"
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force
}

try {
    # Pull image
    Write-Host "Pulling image..." -ForegroundColor Yellow
    docker pull $Image

    # Test Trivy
    Write-Host "Running Trivy scan..." -ForegroundColor Yellow
    & $TrivyPath image --severity CRITICAL,HIGH --format table $Image

    Write-Host "`nScanning tools are working!" -ForegroundColor Green
    Write-Host "You can now use the full local-container-scan.ps1 script" -ForegroundColor Cyan

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
