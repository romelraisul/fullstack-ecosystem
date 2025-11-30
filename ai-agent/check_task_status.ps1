<#
.SYNOPSIS
    Check the status of AI Agent Continuous Evaluation task.
#>

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Agent Task Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $task = Get-ScheduledTask -TaskName "AI Agent Continuous Evaluation" -ErrorAction Stop
    
    Write-Host "Task Name: " -NoNewline -ForegroundColor Yellow
    Write-Host $task.TaskName -ForegroundColor White
    
    Write-Host "State: " -NoNewline -ForegroundColor Yellow
    Write-Host $task.State -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Cyan' })
    
    Write-Host "Description: " -NoNewline -ForegroundColor Yellow
    Write-Host $task.Description -ForegroundColor White
    
    Write-Host ""
    Write-Host "Trigger Details:" -ForegroundColor Cyan
    Write-Host "----------------" -ForegroundColor Cyan
    
    $trigger = $task.Triggers[0]
    Write-Host "  Start Time: " -NoNewline -ForegroundColor Yellow
    Write-Host $trigger.StartBoundary -ForegroundColor White
    
    Write-Host "  Repetition Interval: " -NoNewline -ForegroundColor Yellow
    Write-Host $trigger.Repetition.Interval -ForegroundColor Green
    
    Write-Host "  Repetition Duration: " -NoNewline -ForegroundColor Yellow
    Write-Host $trigger.Repetition.Duration -ForegroundColor White
    
    Write-Host ""
    Write-Host "Recent Task Runs:" -ForegroundColor Cyan
    Write-Host "----------------" -ForegroundColor Cyan
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName "AI Agent Continuous Evaluation"
    Write-Host "  Last Run Time: " -NoNewline -ForegroundColor Yellow
    Write-Host $taskInfo.LastRunTime -ForegroundColor White
    
    Write-Host "  Last Result: " -NoNewline -ForegroundColor Yellow
    $lastResult = if ($taskInfo.LastTaskResult -eq 0) { "Success (0)" } else { "Error ($($taskInfo.LastTaskResult))" }
    $color = if ($taskInfo.LastTaskResult -eq 0) { 'Green' } else { 'Red' }
    Write-Host $lastResult -ForegroundColor $color
    
    Write-Host "  Next Run Time: " -NoNewline -ForegroundColor Yellow
    Write-Host $taskInfo.NextRunTime -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Recent Logs:" -ForegroundColor Cyan
    Write-Host "----------------" -ForegroundColor Cyan
    
    $logsDir = Join-Path $PSScriptRoot "logs"
    $recentLogs = Get-ChildItem "$logsDir\nightly_eval_*.log" | 
                  Sort-Object LastWriteTime -Descending | 
                  Select-Object -First 5
    
    foreach ($log in $recentLogs) {
        $age = (Get-Date) - $log.LastWriteTime
        $ageStr = if ($age.TotalMinutes -lt 60) {
            "$([math]::Round($age.TotalMinutes)) minutes ago"
        } else {
            "$([math]::Round($age.TotalHours, 1)) hours ago"
        }
        
        Write-Host "  $($log.Name) " -NoNewline -ForegroundColor White
        Write-Host "($ageStr)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Task is configured and running!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available tasks:" -ForegroundColor Yellow
    Get-ScheduledTask | Where-Object { $_.TaskName -like '*AI*' } | 
        Select-Object TaskName, State | 
        Format-Table -AutoSize
}
