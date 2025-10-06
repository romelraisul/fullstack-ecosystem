Param(
    [int]$Port = 8081,
    [string]$Secret = 'devsecret'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path '.gov-venv')) {
    Write-Host 'Creating virtual environment (.gov-venv)...'
    python -m venv .gov-venv
}

Write-Host 'Installing requirements (idempotent)...'
./.gov-venv/Scripts/python -m pip install -r governance_app/requirements.txt | Out-Null

$env:WEBHOOK_SECRET = $Secret
$env:PYTHONPATH = (Get-Location).Path

Write-Host "Starting governance app on port $Port"
Start-Process -FilePath ./.gov-venv/Scripts/python -ArgumentList "-m", "uvicorn", "governance_app.app:app", "--port", $Port, "--reload" -NoNewWindow

Start-Sleep -Seconds 2

if (-not (Test-Path '.github/workflows')) { New-Item -ItemType Directory '.github/workflows' | Out-Null }
if (-not (Test-Path '.github/workflows/example.yml')) {
    @'
name: Example
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: someorg/someaction@v1
'@ | Set-Content '.github/workflows/example.yml'
}

$env:GOV_APP_PORT = "$Port"
Write-Host 'Simulating push event...'
./.gov-venv/Scripts/python governance_app/sample_push_event.py

Write-Host 'Done. Query endpoints:'
Write-Host "  curl http://localhost:$Port/healthz"
Write-Host "  curl http://localhost:$Port/runs"
Write-Host "  curl http://localhost:$Port/findings"
Write-Host "  curl http://localhost:$Port/stats"
