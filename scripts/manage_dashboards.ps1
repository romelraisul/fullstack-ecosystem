<#
.SYNOPSIS
  Unified launcher to start/stop/status multiple FastAPI / Node dashboard services.
.DESCRIPTION
  Manages common services in this repository. Writes a dashboards_status.json file
  for the HTML index page to consume.
#>

param(
    [ValidateSet('start', 'stop', 'status', 'restart', 'open', 'generate-index')]
    [string]$Action = 'status'
)

$ErrorActionPreference = 'Stop'

# Root assumed to be the repository directory (script lives in scripts/)
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = 'python'
$StatusFile = Join-Path $RepoRoot 'dashboards_status.json'

# Service definitions (Python scripts) with metadata
$Services = @(
    @{ Name = 'UltimateEnterpriseSummary'; Port = 5099; Script = 'autogen/ultimate_enterprise_summary.py'; Args = ''; Health = '/'; Type = 'python' }
    # Moved AdvancedBackend off conflicting port 8000 to 8011
    @{ Name = 'AdvancedBackend'; Port = 8011; Script = 'autogen/advanced_backend.py'; Args = ''; Health = '/health'; Type = 'python' }
    @{ Name = 'AdvancedMonitoringStack'; Port = 5025; Script = 'autogen/advanced_monitoring_stack.py'; Args = ''; Health = '/'; Type = 'python' }
    @{ Name = 'APIMonetizationPortal'; Port = 5026; Script = 'autogen/api_monetization_portal.py'; Args = ''; Health = '/'; Type = 'python' }
    @{ Name = 'AdvancedSecurityCenter'; Port = 5019; Script = 'autogen/advanced_security_center.py'; Args = ''; Health = '/'; Type = 'python' }
    @{ Name = 'AIMLExpansionSuite'; Port = 5010; Script = 'autogen/ai_ml_expansion_suite.py'; Args = ''; Health = '/'; Type = 'python' }
    @{ Name = 'AdvancedSecurityCompliance'; Port = 5008; Script = 'autogen/advanced_security_compliance.py'; Args = ''; Health = '/'; Type = 'python' }
    @{ Name = 'BlockchainCryptoPlatform'; Port = 5205; Script = 'blockchain_crypto_platform.py'; Args = ''; Health = '/'; Type = 'python' }
)

# PID directory
$PidDir = Join-Path $RepoRoot '.pids'
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir | Out-Null }

# Logs directory for stdout/stderr capture
$LogsDir = Join-Path $RepoRoot '.logs'
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir | Out-Null }

function Get-PidFile($name) { Join-Path $PidDir "$name.pid" }

function Test-PortListening($port) {
    (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $port }).Count -gt 0
}

function Get-ServiceStatus($svc) {
    $pidFile = Get-PidFile $svc.Name
    $svcProcessId = $null
    $running = $false
    if (Test-Path $pidFile) {
        try { $svcProcessId = Get-Content $pidFile -ErrorAction Stop } catch { $svcProcessId = $null }
        if ($svcProcessId) {
            $proc = Get-Process -Id $svcProcessId -ErrorAction SilentlyContinue
            if ($proc) { $running = $true }
        }
    }
    if (-not $running) {
        $running = Test-PortListening $svc.Port
    }
    [PSCustomObject]@{
        Name    = $svc.Name
        Port    = $svc.Port
        PID     = if ($running -and $svcProcessId) { [int]$svcProcessId } else { $null }
        Running = $running
        URL     = "http://localhost:$($svc.Port)"
        Health  = $svc.Health
        Script  = $svc.Script
        Type    = $svc.Type
    }
}

function Start-ServiceDefinition($svc) {
    $status = Get-ServiceStatus $svc
    if ($status.Running) { Write-Host "[SKIP] $($svc.Name) already running on port $($svc.Port)" -ForegroundColor Yellow; return }
    $scriptPath = Join-Path $RepoRoot $svc.Script
    if (-not (Test-Path $scriptPath)) { Write-Host "[MISS] Script not found: $scriptPath" -ForegroundColor Red; return }
    $pidFile = Get-PidFile $svc.Name
    if ($svc.Type -eq 'python') {
        $serviceArgs = @($scriptPath)
        if ($svc.Args) { $serviceArgs += $svc.Args }
        if ($svc.Name -eq 'AdvancedBackend') { $env:ADV_BACKEND_PORT = [string]$svc.Port }
        $logPath = Join-Path $LogsDir ("${($svc.Name)}.log")
        # Use a lightweight powershell wrapper to append stdout+stderr to log
        $argString = ($serviceArgs | ForEach-Object { '"' + $_ + '"' }) -join ' '
        $wrapper = "-NoLogo -NoProfile -Command & { & '" + $Python + "' $argString *>> '" + $logPath + "' }"
        $psi = Start-Process -FilePath powershell.exe -ArgumentList $wrapper -WorkingDirectory $RepoRoot -WindowStyle Minimized -PassThru
        $psi.Id | Out-File -FilePath $pidFile -Encoding ascii -Force
        Write-Host "[START] $($svc.Name) PID=$($psi.Id) Port=$($svc.Port) Log=$logPath" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Unsupported service type: $($svc.Type)" -ForegroundColor Yellow
    }
}

function Stop-ServiceDefinition($svc) {
    $pidFile = Get-PidFile $svc.Name
    if (Test-Path $pidFile) {
        $svcProcessId = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($svcProcessId) {
            $proc = Get-Process -Id $svcProcessId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "[STOP] $($svc.Name) PID=$svcProcessId" -ForegroundColor Cyan
                Stop-Process -Id $svcProcessId -Force -ErrorAction SilentlyContinue
            }
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "[INFO] No PID file for $($svc.Name)" -ForegroundColor DarkGray
    }
}

function Write-StatusFile($statuses) {
    $json = $statuses | ConvertTo-Json -Depth 4
    $json | Out-File -FilePath $StatusFile -Encoding utf8 -Force
    Write-Host "[WRITE] Status file updated: $StatusFile" -ForegroundColor DarkGreen
}

function Invoke-HealthCheck($status) {
    if (-not $status.Running) { return $status | Add-Member -NotePropertyName HealthStatus -NotePropertyValue 'down' -PassThru }
    $uri = "$($status.URL)$($status.Health)".TrimEnd('/')
    $methods = @('Head', 'Get')
    foreach ($m in $methods) {
        try {
            $resp = Invoke-WebRequest -Uri $uri -Method $m -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            $code = $resp.StatusCode
            # Treat 200-399 as up; also tolerate 404/405 meaning server responded
            if ($code -ge 200 -and $code -lt 400) {
                return $status | Add-Member -NotePropertyName HealthStatus -NotePropertyValue 'up' -PassThru
            }
            elseif ($code -in 404, 405) {
                return $status | Add-Member -NotePropertyName HealthStatus -NotePropertyValue 'reachable' -PassThru
            }
            else {
                return $status | Add-Member -NotePropertyName HealthStatus -NotePropertyValue ("code-$code") -PassThru
            }
        }
        catch {
            if ($m -eq 'Get') {
                return $status | Add-Member -NotePropertyName HealthStatus -NotePropertyValue 'error' -PassThru
            }
        }
    }
}

switch ($Action) {
    'start' {
        foreach ($svc in $Services) { Start-ServiceDefinition $svc }
    }
    'stop' {
        foreach ($svc in $Services) { Stop-ServiceDefinition $svc }
    }
    'restart' {
        foreach ($svc in $Services) { Stop-ServiceDefinition $svc }
        Start-Sleep -Seconds 2
        foreach ($svc in $Services) { Start-ServiceDefinition $svc }
        # Grace period for services to bind
        Start-Sleep -Seconds 3
    }
    'open' {
        foreach ($svc in $Services) {
            $status = Get-ServiceStatus $svc
            if ($status.Running) { Start-Process $status.URL }
        }
    }
    'generate-index' { }
    default { }
}

# Always output status at end
$allStatuses = @()
foreach ($svc in $Services) { $allStatuses += (Invoke-HealthCheck (Get-ServiceStatus $svc)) }
Write-StatusFile $allStatuses

$allStatuses | Format-Table Name, Port, Running, HealthStatus, PID, URL

if ($Action -eq 'generate-index') {
    Write-Host "Generate-index action selected; ensure dashboard_index.html reads dashboards_status.json" -ForegroundColor Magenta
}
