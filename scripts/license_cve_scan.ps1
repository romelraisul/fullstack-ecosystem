<#!
.SYNOPSIS
  Generate third-party license inventory and vulnerability (CVE) report.
.DESCRIPTION
  Installs (if needed) pip-licenses and safety, then produces:
    - licenses.json / licenses.txt
    - safety_report.json / safety_report.txt
  Exit code: 0 on success, >0 on tooling failure only (vulns do NOT force non-zero unless --fail-on-high specified).
.PARAMETER FailOnHigh
  If provided (any value), script exits with code 2 when a HIGH/CRITICAL safety vulnerability is detected.
#>
param(
    [switch]$FailOnHigh
)

$ErrorActionPreference = 'Stop'
Write-Host '[license_cve_scan] Starting scan...' -ForegroundColor Cyan

function EnsurePackage {
    param([string]$Name)
    $code = "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$Name') else 1)"
    python -c $code 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $Name" -ForegroundColor Yellow
        pip install $Name --quiet
    }
}

EnsurePackage 'piplicenses'
EnsurePackage 'safety'

# Output directory
$outDir = Join-Path (Get-Location) 'build-reports'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

Write-Host '[license_cve_scan] Generating license reports'
python -m piplicenses --format=json --with-authors --with-urls --with-description --output-file ($outDir + '/licenses.json')
python -m piplicenses --format=plain-vertical --with-authors --with-urls --with-description > ($outDir + '/licenses.txt')

Write-Host '[license_cve_scan] Running safety vulnerability scan'
python -m safety scan -o json > ($outDir + '/safety_report.json') 2>$null
if ($LASTEXITCODE -ne 0) { python -m safety check -o json > ($outDir + '/safety_report.json') }
python -m safety scan > ($outDir + '/safety_report.txt') 2>$null
if ($LASTEXITCODE -ne 0) { python -m safety check > ($outDir + '/safety_report.txt') }

$highCount = 0
try {
    $json = Get-Content ($outDir + '/safety_report.json') -Raw | ConvertFrom-Json
    if ($json.vulnerabilities) {
        foreach ($v in $json.vulnerabilities) {
            if ($v.severity -in @('high', 'critical', 'HIGH', 'CRITICAL')) { $highCount++ }
        }
    }
}
catch { Write-Warning 'Could not parse safety_report.json for severity counts.' }

Write-Host "[license_cve_scan] High/Critical vulnerabilities detected: $highCount" -ForegroundColor Magenta
if ($FailOnHigh -and $highCount -gt 0) {
    Write-Host '[license_cve_scan] Failing build due to high severity vulnerabilities.' -ForegroundColor Red
    exit 2
}

Write-Host '[license_cve_scan] Completed successfully.' -ForegroundColor Green
