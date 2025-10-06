# Code linting script using Ruff and Flake8 for PowerShell
param(
    [switch]$Help,
    [string[]]$Targets = @("autogen", "tests", "scripts", "*.py"),
    [switch]$Fix
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

function Invoke-SafeCommand {
    param($Command, $Description, $AllowFailure = $false)

    Write-Status "`n🔍 $Description..." "Info"
    try {
        $output = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ $Description passed" "Success"
            if ($output) { Write-Host $output }
            return $true
        }
        else {
            throw "Command failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        if ($AllowFailure) {
            Write-Status "⚠️ $Description found issues" "Warning"
        }
        else {
            Write-Status "❌ $Description failed" "Error"
        }
        if ($output) { Write-Host $output }
        return $false
    }
}

if ($Help) {
    Write-Host @"
Code Linting Script

Usage: .\scripts\lint.ps1 [options]

Options:
  -Help           Show this help message
  -Targets        Specify custom targets (default: autogen, tests, scripts, *.py)
  -Fix            Attempt to auto-fix issues where possible

Examples:
  .\scripts\lint.ps1                     # Lint default targets
  .\scripts\lint.ps1 -Fix               # Lint and auto-fix issues
  .\scripts\lint.ps1 -Targets autogen   # Lint only autogen directory
"@
    exit 0
}

Write-Status "🔍 Running code linting..." "Info"

# Build target list
$targetList = @()
foreach ($target in $Targets) {
    if ($target -like "*.*") {
        # Handle file patterns
        $files = Get-ChildItem -Path . -Name $target -File -ErrorAction SilentlyContinue
        $targetList += $files
    }
    elseif (Test-Path $target -PathType Container) {
        # Handle directories
        $targetList += $target
    }
    elseif (Test-Path $target -PathType Leaf) {
        # Handle individual files
        $targetList += $target
    }
}

if ($targetList.Count -eq 0) {
    Write-Status "❌ No Python files found to lint" "Error"
    exit 1
}

$targetsString = $targetList -join " "
Write-Status "Linting targets: $targetsString" "Info"

$results = @()

# Run ruff check (primary linter)
$fixFlag = if ($Fix) { " --fix" } else { "" }
$ruffSuccess = Invoke-SafeCommand "ruff check$fixFlag $targetsString" "Ruff linting" $true
$results += @{ Tool = "Ruff"; Success = $ruffSuccess }

# Run flake8 (secondary linter)
$flake8Success = Invoke-SafeCommand "flake8 $targetsString" "Flake8 linting" $true
$results += @{ Tool = "Flake8"; Success = $flake8Success }

# Run mypy (type checking)
$mypyTargets = if ($targetsString -eq "autogen tests scripts *.py") { "" } else { $targetsString }
$mypySuccess = Invoke-SafeCommand "python scripts/type_check.py $mypyTargets" "mypy type checking" $true
$results += @{ Tool = "mypy"; Success = $mypySuccess }

# Summary
Write-Status "`n📊 Linting Summary:" "Info"
$allPassed = $true
foreach ($result in $results) {
    $status = if ($result.Success) { "✅ PASSED" } else { "❌ FAILED" }
    Write-Host "  $($result.Tool): $status"
    if (-not $result.Success) {
        $allPassed = $false
    }
}

if ($allPassed) {
    Write-Status "`n🎉 All linting checks passed!" "Success"
}
else {
    Write-Status "`n⚠️ Some linting checks found issues. Please review and fix them." "Warning"
    Write-Status "`n💡 Quick fix suggestions:" "Info"
    Write-Host "  1. Run: .\scripts\format.ps1  # Auto-fix formatting issues"
    Write-Host "  2. Run: .\scripts\lint.ps1 -Fix  # Auto-fix some linting issues"
    Write-Host "  3. Run: python scripts/type_check.py --baseline  # Generate mypy baseline"
    Write-Host "  4. Add type annotations to fix mypy issues"
    Write-Host "  5. Manually review and fix remaining issues"
}

exit $(if ($allPassed) { 0 } else { 1 })
