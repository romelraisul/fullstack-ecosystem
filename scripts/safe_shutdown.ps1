<#
.SYNOPSIS
  Perform a "safe" shutdown workflow for the repo before powering off the machine.

.DESCRIPTION
  - Ensures .env is loaded (non-destructive)
  - Optionally aggregates benchmark artifacts
  - Creates a timestamped backup snapshot (ZIP) of key project directories/files
  - Optionally runs git add/commit (if there are staged/unstaged changes)
  - Optionally pushes to the current branch
  - Prompts user for final confirmation before initiating system shutdown

.PARAMETER Aggregate
  Run benchmark aggregation (if artifacts exist) before backup.

.PARAMETER Commit
  Create a commit with a generated message when there are changes.

.PARAMETER Push
  After commit, push to origin current branch.

.PARAMETER BackupDir
  Directory to place generated backups (default: backups)

.PARAMETER DryRun
  Show what would happen without writing or shutting down.

.PARAMETER Force
  Skip final interactive confirmation before shutdown (use with caution).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/safe_shutdown.ps1 -Aggregate -Commit -Push

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/safe_shutdown.ps1 -DryRun

.NOTES
  Requires: PowerShell 5+, git in PATH (for commit/push), zip (Compress-Archive is built-in on Windows).
#>
[CmdletBinding()]
param(
    [switch]$Aggregate,
    [switch]$Commit,
    [switch]$Push,
    [string]$BackupDir = 'backups',
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host "[safe-shutdown] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[safe-shutdown][WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[safe-shutdown][ERROR] $msg" -ForegroundColor Red }

# 1. Load .env if present
if (Test-Path .env) {
    Write-Step 'Loading .env (non-destructive)'
    Get-Content .env | ForEach-Object {
        if ($_ -match '^[A-Za-z_][A-Za-z0-9_]*=') {
            $kv = $_.Split('=', 2)
            $key = $kv[0]
            $val = $kv[1]
            if (-not (Get-Item Env:$key -ErrorAction SilentlyContinue)) {
                Set-Item -Path Env:$key -Value $val
            }
        }
    }
}

# 2. Optional aggregation
if ($Aggregate) {
    if (Test-Path artifacts) {
        $glob = 'artifacts/quantile_bench_*.json'
        $jsonOut = 'artifacts/aggregate.json'
        $mdOut = 'artifacts/aggregate.md'
        if (Get-ChildItem -Path artifacts -Filter 'quantile_bench_*.json' -ErrorAction SilentlyContinue) {
            Write-Step "Aggregating benchmarks ($glob)"
            $cmd = "python scripts/aggregate_quantile_benchmarks.py --input-glob `"$glob`" --json-out $jsonOut --markdown-out $mdOut"
            if ($DryRun) { Write-Host "DRYRUN: $cmd" } else { Invoke-Expression $cmd }
        }
        else {
            Write-Warn 'No benchmark JSON artifacts found to aggregate.'
        }
    }
    else {
        Write-Warn 'artifacts/ directory not found.'
    }
}

# 3. Prepare backup directory
if (-not (Test-Path $BackupDir)) {
    if ($DryRun) { Write-Host "DRYRUN: New-Item -ItemType Directory $BackupDir" } else { New-Item -ItemType Directory $BackupDir | Out-Null }
}

$timestamp = Get-Date -Format yyyyMMdd_HHmmss
$backupName = "snapshot_$timestamp.zip"
$backupPath = Join-Path $BackupDir $backupName

# Choose important content (exclude heavy or transient patterns already ignored)
$include = @(
    'README.md', 'docs', 'scripts', 'backend', 'tests', '.env.example', 'Makefile', 'requirements.txt', '.github/workflows', 'alerts_taxonomy.json'
)

# Filter only existing
$existing = $include | Where-Object { Test-Path $_ }
if (-not $existing) {
    Write-Warn 'No include targets exist; skipping backup.'
}
else {
    Write-Step "Creating backup archive: $backupPath"
    if ($DryRun) {
        Write-Host "DRYRUN: Compress-Archive -Path $($existing -join ',') -DestinationPath $backupPath -Force"
    }
    else {
        Compress-Archive -Path $existing -DestinationPath $backupPath -Force
    }
}

# 4. Git commit (optional)
$didCommit = $false
if ($Commit) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warn 'git not found; skipping commit.'
    }
    else {
        $status = git status --porcelain
        if ($status) {
            Write-Step 'Staging and committing changes'
            if ($DryRun) {
                Write-Host 'DRYRUN: git add -A'
                Write-Host "DRYRUN: git commit -m 'safe shutdown snapshot $timestamp'"
            }
            else {
                git add -A
                git commit -m "safe shutdown snapshot $timestamp"
                $didCommit = $true
            }
        }
        else {
            Write-Step 'No changes to commit.'
        }
    }
}

# 5. Git push (optional)
if ($Push -and $didCommit) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warn 'git not found; cannot push.'
    }
    else {
        $branch = (git rev-parse --abbrev-ref HEAD).Trim()
        Write-Step "Pushing branch $branch"
        if ($DryRun) {
            Write-Host "DRYRUN: git push origin $branch"
        }
        else {
            git push origin $branch
        }
    }
}
elseif ($Push -and -not $didCommit) {
    Write-Warn 'Push requested but nothing was committed in this run.'
}

# 6. Final confirmation & shutdown
if ($DryRun) {
    Write-Step 'Dry run complete. No shutdown performed.'
    exit 0
}

if (-not $Force) {
    $confirm = Read-Host 'Proceed with system shutdown? (y/N)'
    if ($confirm -notin @('y', 'Y', 'yes', 'YES')) {
        Write-Step 'Aborting without shutdown.'
        exit 0
    }
}

Write-Step 'Initiating system shutdown (Windows) in 30 seconds...'
shutdown /s /t 30 /c "Safe shutdown initiated after repo snapshot."
