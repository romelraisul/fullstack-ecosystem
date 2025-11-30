# Setup Python Virtual Environment for AI Agent
# Run this first to prepare local development environment

$ErrorActionPreference = "Stop"

Write-Host "🐍 Setting up Python Virtual Environment..." -ForegroundColor Cyan

$BasePath = 'G:\My Drive\Automations'
$VENV_PATH = (Join-Path $BasePath 'aiauto_venv')
$REQUIREMENTS = (Join-Path $BasePath 'ai-agent/requirements.txt')

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Remove old venv if exists but broken
if (Test-Path $VENV_PATH) {
    if (-not (Test-Path "$VENV_PATH\Scripts\python.exe")) {
        Write-Host "⚠ Removing broken venv..." -ForegroundColor Yellow
        Remove-Item -Path $VENV_PATH -Recurse -Force
    }
}

# Create new venv
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $VENV_PATH
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Cyan
& "$VENV_PATH\Scripts\python.exe" -m pip install --upgrade pip --quiet

# Install dependencies with --pre flag (required for Microsoft Agent Framework)
Write-Host "📦 Installing AI agent dependencies (this may take 2-3 minutes)..." -ForegroundColor Cyan
& "$VENV_PATH\Scripts\python.exe" -m pip install --pre -r $REQUIREMENTS

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Python environment setup complete!" -ForegroundColor Green
    Write-Host "`nTo activate venv:" -ForegroundColor Cyan
    Write-Host "  $VENV_PATH\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "`nTo test AI agent:" -ForegroundColor Cyan
    Write-Host "  cd $(Join-Path $BasePath 'ai-agent')" -ForegroundColor Yellow
    Write-Host "  ..\aiauto_venv\Scripts\python.exe infrastructure_agent.py" -ForegroundColor Yellow
    Write-Host "Base path: $BasePath" -ForegroundColor Yellow
} else {
    Write-Host "`n✗ Installation failed!" -ForegroundColor Red
    exit 1
}
