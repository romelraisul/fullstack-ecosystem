<#
.SYNOPSIS
    Register a Windows Scheduled Task to run AI agent evaluation continuously.

.DESCRIPTION
    Creates a scheduled task that runs evaluation every minute for rapid completion.
    Logs are written to ai-agent\logs\nightly_eval_<date>.log
    
.PARAMETER IntervalMinutes
    Interval in minutes (default: 1 for every minute)

.EXAMPLE
    .\schedule_nightly_eval.ps1
    .\schedule_nightly_eval.ps1 -IntervalMinutes 5
#>

param(
    [int]$IntervalMinutes = 1
)

$ErrorActionPreference = 'Stop'

# Ensure we're running as Administrator (self-elevate if needed)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Elevation required; relaunching with admin..." -ForegroundColor Yellow
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $escapedPath = $PSCommandPath -replace '"','`"'
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$escapedPath`" -IntervalMinutes $IntervalMinutes"
    $psi.Verb = "runas"
    try {
        [System.Diagnostics.Process]::Start($psi) | Out-Null
    } catch {
        Write-Error "Elevation was canceled or failed: $($_.Exception.Message)"
    }
    exit
}

# Paths
$scriptRoot = $PSScriptRoot
$helperScript = Join-Path $scriptRoot "run_eval_helper.ps1"
$logsDir = Join-Path $scriptRoot "logs"
$wrapperScript = Join-Path $scriptRoot "nightly_eval_wrapper.ps1"

# Verify helper exists
if (-not (Test-Path $helperScript)) {
    Write-Error "Helper script not found: $helperScript"
    exit 1
}

# Create logs directory
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "Created logs directory: $logsDir" -ForegroundColor Green
}

# Create wrapper script that handles logging
$wrapperContent = @"
`$ErrorActionPreference = 'Continue'
`$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
`$logFile = Join-Path '$logsDir' "nightly_eval_`$timestamp.log"

# Start transcript
Start-Transcript -Path `$logFile -Append

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Nightly AI Agent Evaluation" -ForegroundColor Cyan
Write-Host "Started: `$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    # Run evaluation
    & '$helperScript' -FreshResponses
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Evaluation completed successfully" -ForegroundColor Green
    Write-Host "Finished: `$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Evaluation failed: `$(`$_.Exception.Message)" -ForegroundColor Red
    Write-Host "Finished: `$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
} finally {
    Stop-Transcript
}
"@

Set-Content -Path $wrapperScript -Value $wrapperContent -Force
Write-Host "Created wrapper script: $wrapperScript" -ForegroundColor Green

# Task configuration
$taskName = "AI Agent Continuous Evaluation"
$taskDescription = "Runs AI agent evaluation every $IntervalMinutes minute(s) and logs results"
$taskAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$wrapperScript`"" `
    -WorkingDirectory $scriptRoot

# Create trigger that repeats every X minutes indefinitely
$taskTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)

# Run whether user is logged on or not, with highest privileges
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Task settings
$taskSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Register the task
$task = Register-ScheduledTask `
    -TaskName $taskName `
    -Description $taskDescription `
    -Action $taskAction `
    -Trigger $taskTrigger `
    -Principal $taskPrincipal `
    -Settings $taskSettings

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Scheduled Task Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Task Name: $taskName" -ForegroundColor Cyan
Write-Host "Run Frequency: Every $IntervalMinutes minute(s)" -ForegroundColor Cyan
Write-Host "Log Location: $logsDir\nightly_eval_<timestamp>.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "Management commands:" -ForegroundColor Yellow
Write-Host "  View task:    Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "  Run now:      Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "  Disable:      Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "  Enable:       Enable-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "  Remove:       Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor White
Write-Host ""
Write-Host "To test immediately:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host ""
