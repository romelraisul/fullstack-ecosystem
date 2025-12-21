$WindowTitle = "Hostamar AI Watchdog"
$Host.UI.RawUI.WindowTitle = $WindowTitle

Write-Host "🐶 Hostamar AI Watchdog Started (Resource Optimized)" -ForegroundColor Cyan
Write-Host "Monitoring background agents..." -ForegroundColor Gray

while ($true) {
    # Check for specific agent scripts in the command line of running python processes
    $agents = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { 
        $_.CommandLine -match "chief_orchestrator|infrastructure_agent|marketing_agent|monitoring_agent" 
    }
    
    if (-not $agents) {
        Write-Host "[$(Get-Date)] ⚠️  Agents not detected. Booting office..." -ForegroundColor Yellow
        python "G:\My Drive\Automations\ai-agent\launch_office.py"
    } else {
        # Check if we have all 4 (roughly)
        $count = ($agents | Measure-Object).Count
        Write-Host " [Agents Active: $count] " -NoNewline -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 60
}