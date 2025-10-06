# Type checking script using mypy for PowerShell
param(
    [switch]$Help,
    [string[]]$Targets = @(),
    [switch]$Baseline
)

function Write-Status {
    param($Message, $Type = "Info")
    $color = switch ($Type) {
        "Success" { "Green" }
        "Error" { "Red" }
        "Warning" { "Yellow" }
        default { "White" }
    }
    Write-Host $Message -ForegroundColor $color
}

if ($Help) {
    Write-Host @"
Type Checking Script using mypy

Usage: .\scripts\type_check.ps1 [options]

Options:
  -Help           Show this help message
  -Targets        Specify custom targets (default: key scripts)
  -Baseline       Generate baseline report of current type issues

Examples:
  .\scripts\type_check.ps1                     # Check default targets
  .\scripts\type_check.ps1 -Baseline          # Generate baseline report
  .\scripts\type_check.ps1 -Targets scripts/  # Check only scripts directory
"@
    exit 0
}

Write-Status "🔍 Running type checking with mypy..." "Info"

# Build command
$cmd = "python scripts/type_check.py"

if ($Baseline) {
    $cmd += " --baseline"
}
elseif ($Targets.Count -gt 0) {
    $targetsString = $Targets -join " "
    $cmd += " $targetsString"
}

Write-Status "Executing: $cmd" "Info"

try {
    $output = Invoke-Expression $cmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ Type checking completed successfully" "Success"
        if ($output) { Write-Host $output }
        exit 0
    }
    else {
        Write-Status "⚠️ Type checking found issues" "Warning"
        if ($output) { Write-Host $output }
        exit 1
    }
}
catch {
    Write-Status "❌ Type checking failed: $($_.Exception.Message)" "Error"
    exit 1
}
