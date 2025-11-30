# Nightly Evaluation Logs

This directory contains logs from automated nightly evaluation runs.

## Log Files

Each evaluation run creates a timestamped log file:
- Format: `nightly_eval_YYYY-MM-DD_HHmmss.log`
- Contains complete output from the evaluation process
- Includes timestamps, model info, evaluation results, and any errors

## Log Retention

Consider periodically cleaning old logs:

```powershell
# Keep only last 30 days of logs
Get-ChildItem .\logs -Filter "nightly_eval_*.log" | 
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
  Remove-Item
```

## Viewing Recent Logs

```powershell
# View latest log
Get-Content (Get-ChildItem .\logs -Filter "nightly_eval_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

# View last 5 logs
Get-ChildItem .\logs -Filter "nightly_eval_*.log" | 
  Sort-Object LastWriteTime -Descending | 
  Select-Object -First 5 | 
  ForEach-Object { Write-Host $_.Name -ForegroundColor Cyan; Get-Content $_.FullName }
```
