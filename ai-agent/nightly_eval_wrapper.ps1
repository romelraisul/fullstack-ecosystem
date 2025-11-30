$ErrorActionPreference = 'Continue'
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$BasePath = 'G:\My Drive\Automations'
$logFile = Join-Path (Join-Path $BasePath 'ai-agent/logs') "nightly_eval_$timestamp.log"

# Start transcript
Start-Transcript -Path $logFile -Append

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Nightly AI Agent Evaluation" -ForegroundColor Cyan
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    # Run evaluation
    & (Join-Path $BasePath 'ai-agent/run_eval_helper.ps1') -FreshResponses
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Evaluation completed successfully" -ForegroundColor Green
    Write-Host "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Evaluation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
} finally {
    Stop-Transcript
}
