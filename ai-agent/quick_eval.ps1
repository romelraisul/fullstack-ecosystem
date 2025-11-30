# Quick Evaluation Runner
param([string]$Token)

$env:GITHUB_TOKEN = $Token
$BasePath = 'G:\My Drive\Automations'
$venvPython = (Join-Path $BasePath '.venv/Scripts/python.exe')

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $BasePath '.venv')
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet --pre -r "$PSScriptRoot\requirements.txt"

Write-Host "`nRunning evaluation..." -ForegroundColor Green
& $venvPython "$PSScriptRoot\evaluate_agent.py"

Write-Host "`nDone! Check ai-agent\evaluation\results\ | Base: $BasePath" -ForegroundColor Cyan
