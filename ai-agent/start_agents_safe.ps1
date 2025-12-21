# Safe Agent Launcher
# This script ensures credentials exist before launching the AI Office.

$EnvPath = "$PSScriptRoot\.env"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   HOSTAMAR AI OFFICE: PRE-FLIGHT CHECK   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check for .env file
if (-not (Test-Path $EnvPath)) {
    Write-Host "⚠️  Configuration file (.env) is missing!" -ForegroundColor Yellow
    Write-Host "Auto-generating MOCK credentials for immediate launch..." -ForegroundColor Gray
    
    # Create mock .env to prevent crash
    Set-Content -Path $EnvPath -Value "GITHUB_TOKENS=MOCK_TOKEN_FOR_BOOT_ONLY"
    Write-Host "✅ Created .env with placeholder. Update it later for AI functionality." -ForegroundColor Green
} else {
    Write-Host "✅ Configuration file found." -ForegroundColor Green
}

# 2. Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Gray
try {
    python --version | Out-Null
    Write-Host "✅ Python is accessible." -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not found in PATH." -ForegroundColor Red
    exit 1
}

# 3. Launch the main python script
Write-Host "🚀 Launching AI Office..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
python "$PSScriptRoot\launch_office.py"
