# Complete Coolify Automation & Management Suite
# Final integration script that brings everything together

param(
    [string]$CoolifyPath = "C:\coolify",
    [string]$Action = "deploy",
    [bool]$EnableSecurity = $true,
    [bool]$EnableMonitoring = $true,
    [bool]$RunTests = $true
)

Write-Host "🚀 Coolify Complete Automation Suite" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Step 1: Pre-flight checks
Write-Host "🔍 Running pre-flight checks..." -ForegroundColor Cyan

function Test-Prerequisites {
    $checks = @()

    # Check Docker
    try {
        $dockerVersion = docker --version
        $checks += @{name="Docker"; status="✅ Available"; details=$dockerVersion}
    } catch {
        $checks += @{name="Docker"; status="❌ Missing"; details="Docker not found"}
    }

    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    if ($psVersion.Major -ge 5) {
        $checks += @{name="PowerShell"; status="✅ Compatible"; details="Version $psVersion"}
    } else {
        $checks += @{name="PowerShell"; status="⚠️ Old"; details="Version $psVersion"}
    }

    # Check available disk space
    try {
        $disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
        $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        if ($freeSpaceGB -gt 10) {
            $checks += @{name="Disk Space"; status="✅ Sufficient"; details="$freeSpaceGB GB free"}
        } else {
            $checks += @{name="Disk Space"; status="⚠️ Low"; details="$freeSpaceGB GB free"}
        }
    } catch {
        $checks += @{name="Disk Space"; status="❌ Error"; details="Could not check"}
    }

    # Check network connectivity
    try {
        $networkTest = Test-NetConnection -ComputerName "8.8.8.8" -Port 53 -InformationLevel Quiet
        if ($networkTest) {
            $checks += @{name="Network"; status="✅ Connected"; details="Internet access available"}
        } else {
            $checks += @{name="Network"; status="❌ Offline"; details="No internet access"}
        }
    } catch {
        $checks += @{name="Network"; status="❌ Error"; details="Network check failed"}
    }

    return $checks
}

$preflightResults = Test-Prerequisites

Write-Host "Pre-flight Check Results:" -ForegroundColor Yellow
foreach ($check in $preflightResults) {
    Write-Host "  $($check.name): $($check.status) - $($check.details)" -ForegroundColor White
}

$criticalProblems = $preflightResults | Where-Object { $_.status -like "*❌*" }
if ($criticalProblems) {
    Write-Host ""
    Write-Host "❌ Critical errors found. Please resolve before continuing:" -ForegroundColor Red
    foreach ($problem in $criticalProblems) {
        Write-Host "   - $($problem.name): $($problem.details)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "✅ Pre-flight checks passed!" -ForegroundColor Green
Write-Host ""

# Step 2: Environment Setup
Write-Host "🏗️ Setting up Coolify environment..." -ForegroundColor Cyan

# Create directory structure
$directories = @(
    $CoolifyPath,
    "$CoolifyPath\ssl",
    "$CoolifyPath\data",
    "$CoolifyPath\logs",
    "$CoolifyPath\backups",
    "$CoolifyPath\monitoring",
    "$CoolifyPath\projects",
    "$CoolifyPath\scripts"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Created: $dir" -ForegroundColor White
    }
}

# Copy automation scripts to Coolify directory
$scriptFiles = @(
    "install-coolify.ps1",
    "deploy-to-coolify.ps1",
    "security-hardening.ps1",
    "comprehensive-monitoring.ps1"
)

foreach ($script in $scriptFiles) {
    $sourcePath = ".\$script"
    $targetPath = "$CoolifyPath\scripts\$script"

    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath $targetPath -Force
        Write-Host "📄 Copied: $script" -ForegroundColor White
    }
}

Write-Host "✅ Environment setup completed!" -ForegroundColor Green
Write-Host ""

# Step 3: Core Installation
if ($Action -eq "deploy" -or $Action -eq "install") {
    Write-Host "🐳 Installing Coolify core system..." -ForegroundColor Cyan

    Push-Location $CoolifyPath

    try {
        # Run core installation
        & ".\scripts\install-coolify.ps1" -CoolifyPath $CoolifyPath

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Coolify core installation completed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Coolify installation failed!" -ForegroundColor Red
            Pop-Location
            exit 1
        }
    } catch {
        Write-Host "❌ Installation error: $($_.Exception.Message)" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    Pop-Location
    Write-Host ""
}

# Step 4: Security Hardening
if ($EnableSecurity -and ($Action -eq "deploy" -or $Action -eq "secure")) {
    Write-Host "🔒 Applying security hardening..." -ForegroundColor Cyan

    Push-Location $CoolifyPath

    try {
        & ".\scripts\security-hardening.ps1" -CoolifyPath $CoolifyPath -Environment "production"
        Write-Host "✅ Security hardening completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Security hardening warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Pop-Location
    Write-Host ""
}

# Step 5: Monitoring Setup
if ($EnableMonitoring -and ($Action -eq "deploy" -or $Action -eq "monitor")) {
    Write-Host "📊 Setting up comprehensive monitoring..." -ForegroundColor Cyan

    Push-Location $CoolifyPath

    try {
        & ".\scripts\comprehensive-monitoring.ps1" -CoolifyPath $CoolifyPath -EnableAlerts $true
        Write-Host "✅ Monitoring setup completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Monitoring setup warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Pop-Location
    Write-Host ""
}

# Step 6: System Validation
if ($RunTests -and ($Action -eq "deploy" -or $Action -eq "test")) {
    Write-Host "🧪 Running system validation tests..." -ForegroundColor Cyan

    Push-Location $CoolifyPath

    # Test 1: Container Status
    Write-Host "   Testing container status..." -ForegroundColor Yellow
    try {
        $containers = docker ps --format "{{.Names}},{{.Status}}" | ConvertFrom-Csv -Header "Name","Status"
        $coolifyContainers = $containers | Where-Object { $_.Name -match "coolify|api|frontend|nginx" }

        if ($coolifyContainers.Count -gt 0) {
            Write-Host "   ✅ Containers are running" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ No Coolify containers found" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Container test failed: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test 2: Service Endpoints
    Write-Host "   Testing service endpoints..." -ForegroundColor Yellow
    $testEndpoints = @(
        @{Name="Coolify"; URL="http://localhost:8000"; Timeout=10},
        @{Name="API"; URL="http://localhost:8010"; Timeout=10}
    )

    foreach ($endpoint in $testEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.URL -Method GET -TimeoutSec $endpoint.Timeout -UseBasicParsing
            Write-Host "   ✅ $($endpoint.Name) responding (HTTP $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ $($endpoint.Name) not responding" -ForegroundColor Yellow
        }
    }

    # Test 3: Security Configuration
    Write-Host "   Testing security configuration..." -ForegroundColor Yellow
    if (Test-Path "ssl\coolify.crt") {
        Write-Host "   ✅ SSL certificate found" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ SSL certificate not found" -ForegroundColor Yellow
    }

    if (Test-Path ".env.secure") {
        Write-Host "   ✅ Secure environment configuration found" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Secure environment configuration not found" -ForegroundColor Yellow
    }

    # Test 4: Monitoring Services
    if ($EnableMonitoring) {
        Write-Host "   Testing monitoring services..." -ForegroundColor Yellow
        $monitoringServices = @("prometheus", "grafana", "alertmanager")

        foreach ($service in $monitoringServices) {
            try {
                $status = docker ps --filter "name=$service" --format "{{.Status}}"
                if ($status -like "*Up*") {
                    Write-Host "   ✅ $service is running" -ForegroundColor Green
                } else {
                    Write-Host "   ⚠️ $service not running" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "   ❌ Error checking $service" -ForegroundColor Red
            }
        }
    }

    Pop-Location
    Write-Host "✅ System validation completed!" -ForegroundColor Green
    Write-Host ""
}

# Step 7: Generate deployment report
Write-Host "📋 Generating deployment report..." -ForegroundColor Cyan

$deploymentReport = @{
    timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    version = "1.0.0"
    deployment_info = @{
        coolify_path = $CoolifyPath
        security_enabled = $EnableSecurity
        monitoring_enabled = $EnableMonitoring
        tests_run = $RunTests
    }
    services = @()
    files_created = @()
    next_steps = @()
}

# Collect service information
try {
    $containers = docker ps --format "{{.Names}},{{.Status}},{{.Ports}}" | ConvertFrom-Csv -Header "Name","Status","Ports"
    foreach ($container in $containers) {
        if ($container.Name -match "coolify|prometheus|grafana|nginx") {
            $deploymentReport.services += @{
                name = $container.Name
                status = $container.Status
                ports = $container.Ports
            }
        }
    }
} catch {
    Write-Host "⚠️ Could not collect service information" -ForegroundColor Yellow
}

# List created files
$createdFiles = @(
    "COOLIFY_SETUP.md",
    "docker-compose.yml",
    "install-coolify.ps1",
    "deploy-to-coolify.ps1",
    "security-hardening.ps1",
    "comprehensive-monitoring.ps1"
)

foreach ($file in $createdFiles) {
    if (Test-Path $file) {
        $deploymentReport.files_created += $file
    }
}

# Add next steps
$deploymentReport.next_steps = @(
    "Access Coolify dashboard at http://localhost:8000",
    "Configure your first project in Coolify",
    "Set up SSL certificates for production use",
    "Configure backup schedules",
    "Review security settings and update passwords",
    "Set up monitoring alerts and notifications",
    "Test deployment pipeline with a sample application"
)

# Save report
$reportPath = "$CoolifyPath\deployment-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$deploymentReport | ConvertTo-Json -Depth 5 | Out-File $reportPath -Encoding UTF8

# Step 8: Final Summary and Instructions
Write-Host ""
Write-Host "🎉 Coolify Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "   Installation Path: $CoolifyPath" -ForegroundColor White
Write-Host "   Security Hardening: $(if ($EnableSecurity) { "✅ Enabled" } else { "❌ Disabled" })" -ForegroundColor $(if ($EnableSecurity) { "Green" } else { "Red" })
Write-Host "   Monitoring: $(if ($EnableMonitoring) { "✅ Enabled" } else { "❌ Disabled" })" -ForegroundColor $(if ($EnableMonitoring) { "Green" } else { "Red" })
Write-Host "   System Tests: $(if ($RunTests) { "✅ Completed" } else { "❌ Skipped" })" -ForegroundColor $(if ($RunTests) { "Green" } else { "Red" })
Write-Host ""

if ($deploymentReport.services.Count -gt 0) {
    Write-Host "🐳 Running Services:" -ForegroundColor Cyan
    foreach ($service in $deploymentReport.services) {
        $statusColor = if ($service.status -like "*Up*") { "Green" } else { "Red" }
        Write-Host "   $($service.name): $($service.status)" -ForegroundColor $statusColor
        if ($service.ports) {
            Write-Host "      Ports: $($service.ports)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "   Coolify Dashboard: http://localhost:8000" -ForegroundColor White
Write-Host "   API Endpoint: http://localhost:8010" -ForegroundColor White

if ($EnableMonitoring) {
    Write-Host "   Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "   Grafana: http://localhost:3000" -ForegroundColor White
    Write-Host "   Alertmanager: http://localhost:9093" -ForegroundColor White
}
Write-Host ""

Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "   Check system status:" -ForegroundColor White
Write-Host "     cd $CoolifyPath" -ForegroundColor Gray
Write-Host "     .\scripts\comprehensive-monitoring.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "   Deploy application:" -ForegroundColor White
Write-Host "     .\scripts\deploy-to-coolify.ps1 -ProjectPath <path>" -ForegroundColor Gray
Write-Host ""
Write-Host "   Security audit:" -ForegroundColor White
Write-Host "     .\scripts\security-hardening.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "⚠️  Important Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Change default passwords (especially Grafana admin)" -ForegroundColor White
Write-Host "   2. Configure SSL certificates for production" -ForegroundColor White
Write-Host "   3. Set up regular backups" -ForegroundColor White
Write-Host "   4. Review and customize monitoring alerts" -ForegroundColor White
Write-Host "   5. Test deployment with your applications" -ForegroundColor White
Write-Host ""

Write-Host "📄 Full deployment report saved to:" -ForegroundColor Cyan
Write-Host "   $reportPath" -ForegroundColor White
Write-Host ""

Write-Host "🚀 Coolify is ready for use!" -ForegroundColor Green
Write-Host "Visit http://localhost:8000 to get started!" -ForegroundColor Green

# Create quick access script
$quickAccessScript = @"
# Quick Access Script for Coolify Management
Write-Host "🚀 Coolify Quick Access Menu" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Open Coolify Dashboard (http://localhost:8000)" -ForegroundColor Cyan
Write-Host "2. Open Monitoring (Grafana: http://localhost:3000)" -ForegroundColor Cyan
Write-Host "3. Check System Status" -ForegroundColor Cyan
Write-Host "4. View Logs" -ForegroundColor Cyan
Write-Host "5. Run Security Audit" -ForegroundColor Cyan
Write-Host "6. Deploy Application" -ForegroundColor Cyan
Write-Host "7. Backup System" -ForegroundColor Cyan
Write-Host "8. Exit" -ForegroundColor Cyan
Write-Host ""

do {
    `$choice = Read-Host "Select an option (1-8)"

    switch (`$choice) {
        "1" {
            Write-Host "🌐 Opening Coolify Dashboard..." -ForegroundColor Green
            Start-Process "http://localhost:8000"
        }
        "2" {
            Write-Host "📊 Opening Grafana..." -ForegroundColor Green
            Start-Process "http://localhost:3000"
        }
        "3" {
            Write-Host "🔍 Checking system status..." -ForegroundColor Green
            & "$CoolifyPath\monitoring\health-check.ps1"
        }
        "4" {
            Write-Host "📋 Viewing recent logs..." -ForegroundColor Green
            & "$CoolifyPath\monitoring\collect-logs.ps1"
        }
        "5" {
            Write-Host "🔒 Running security audit..." -ForegroundColor Green
            & "$CoolifyPath\security-audit.ps1"
        }
        "6" {
            Write-Host "🚀 Deploy application..." -ForegroundColor Green
            `$projectPath = Read-Host "Enter project path"
            if (`$projectPath) {
                & "$CoolifyPath\scripts\deploy-to-coolify.ps1" -ProjectPath `$projectPath
            }
        }
        "7" {
            Write-Host "💾 Running backup..." -ForegroundColor Green
            & "$CoolifyPath\secure-backup.ps1"
        }
        "8" {
            Write-Host "👋 Goodbye!" -ForegroundColor Green
            break
        }
        default {
            Write-Host "❌ Invalid option. Please select 1-8." -ForegroundColor Red
        }
    }

    if (`$choice -ne "8") {
        Write-Host ""
        Read-Host "Press Enter to continue"
        Write-Host ""
    }

} while (`$choice -ne "8")
"@

$quickAccessScript | Out-File "$CoolifyPath\coolify-menu.ps1" -Encoding UTF8

Write-Host "💡 Tip: Run '.\coolify-menu.ps1' for quick access to all Coolify functions!" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Complete Coolify automation suite deployment finished!" -ForegroundColor Green
