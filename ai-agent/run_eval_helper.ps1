<#
Automated evaluator runner
- Loads .env
- Ensures fresh responses (optional)
- Runs evaluation and retries on transient errors (e.g., rate limit) up to a max
Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<path>\run_eval_helper.ps1"
#>

param(
  [switch]$FreshResponses,
  [int]$MaxRetries = 2
)
$ErrorActionPreference = 'Stop'

# 1) Load environment
$envFile = Join-Path $PSScriptRoot '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#') { return }
        if ($_ -match '^\s*$') { return }
        $parts = $_ -split '=',2
        if ($parts.Length -eq 2) { Set-Item -Path Env:$($parts[0].Trim()) -Value $parts[1].Trim() }
    }
}

# 2) Optionally remove previous responses
if ($FreshResponses.IsPresent) {
  $resp = Join-Path $PSScriptRoot 'evaluation\\agent_responses.jsonl'
  Remove-Item -Path $resp -ErrorAction SilentlyContinue
}

# 3) Run evaluation with limited retries on failures
$runner = Join-Path $PSScriptRoot 'run.ps1'
if (-not (Test-Path $runner)) {
    Write-Error "Runner script not found: $runner"
}

for ($i = 0; $i -le $MaxRetries; $i++) {
    try {
        & $runner -Mode evaluate -Bootstrap
        break
    } catch {
        Write-Warning "Evaluation failed (attempt $i of $MaxRetries): $($_.Exception.Message)"
        if ($i -ge $MaxRetries) { throw }
        Start-Sleep -Seconds 3
    }
}

Write-Host "Automation complete." -ForegroundColor Green
