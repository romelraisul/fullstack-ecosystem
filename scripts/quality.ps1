# Combined code quality script for PowerShell
param(
    [switch]$Help,
    [string[]]$Targets = @("autogen", "tests", "scripts", "*.py"),
    [switch]$Fix,
    [switch]$SkipFormat,
    [switch]$SkipLint,
    [switch]$SkipType
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

function Invoke-Script {
    param($ScriptName, $Description, $Arguments = @())

    Write-Host "`n$('='*60)"
    Write-Status "🚀 $Description" "Info"
    Write-Host $('='*60)

    $scriptPath = Join-Path $PSScriptRoot $ScriptName
    try {
        $argList = @($scriptPath) + $Arguments
        & powershell @argList
        if ($LASTEXITCODE -eq 0) {
            Write-Status "`n✅ $Description completed successfully" "Success"
            return $true
        } else {
            throw "Script failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        Write-Status "`n❌ $Description failed" "Error"
        return $false
    }
}

if ($Help) {
    Write-Host @"
Combined Code Quality Script

Usage: .\scripts\quality.ps1 [options]

Options:
  -Help           Show this help message
  -Targets        Specify custom targets (default: autogen, tests, scripts, *.py)
  -Fix            Attempt to auto-fix issues where possible
  -SkipFormat     Skip the formatting step
  -SkipLint       Skip the linting step
  -SkipType       Skip the type checking step

Examples:
  .\scripts\quality.ps1                     # Run full quality check
  .\scripts\quality.ps1 -Fix               # Run with auto-fix
  .\scripts\quality.ps1 -SkipFormat        # Only run linting and type checking
  .\scripts\quality.ps1 -SkipType          # Skip type checking
  .\scripts\quality.ps1 -Targets autogen   # Check only autogen directory

Type checking notes:
  - Type checking generates a baseline report (mypy-baseline.txt)
  - Use scripts/type_check.ps1 -Baseline to regenerate baseline
  - Type checking targets: scripts/, autogen/backend/, src/, tests/
"@
    exit 0
}

Write-Status "🎯 Running comprehensive code quality checks..." "Info"

$formatSuccess = $true
$lintSuccess = $true
$typeSuccess = $true

# Prepare arguments
$targetArgs = @()
if ($Targets -and $Targets.Count -gt 0 -and $Targets[0] -ne "autogen,tests,scripts,*.py") {
    $targetArgs += "-Targets"
    $targetArgs += $Targets
}

# Run formatting first (unless skipped)
if (-not $SkipFormat) {
    $formatArgs = $targetArgs
    $formatSuccess = Invoke-Script "format.ps1" "Code Formatting" $formatArgs
}

# Run linting after formatting (unless skipped)
if (-not $SkipLint) {
    $lintArgs = $targetArgs
    if ($Fix) {
        $lintArgs += "-Fix"
    }
    $lintSuccess = Invoke-Script "lint.ps1" "Code Linting" $lintArgs
}

# Run type checking after linting (unless skipped)
if (-not $SkipType) {
    $typeArgs = @()  # Type checking uses its own targets
    $typeSuccess = Invoke-Script "type_check.ps1" "Type Checking" $typeArgs
}

# Summary
Write-Host "`n$('='*60)"
Write-Status "📊 FINAL SUMMARY" "Info"
Write-Host $('='*60)

if (-not $SkipFormat) {
    $formatStatus = if ($formatSuccess) { "✅ PASSED" } else { "❌ FAILED" }
    Write-Host "🎨 Formatting: $formatStatus"
}

if (-not $SkipLint) {
    $lintStatus = if ($lintSuccess) { "✅ PASSED" } else { "❌ FAILED" }
    Write-Host "🔍 Linting:    $lintStatus"
}

if (-not $SkipType) {
    $typeStatus = if ($typeSuccess) { "✅ PASSED" } else { "❌ FAILED" }
    Write-Host "🔍 Type Check: $typeStatus"
}

$overallSuccess = $formatSuccess -and $lintSuccess -and $typeSuccess

if ($overallSuccess) {
    Write-Status "`n🎉 All code quality checks passed! Your code is ready to go! 🚀" "Success"
} else {
    Write-Status "`n⚠️ Some code quality checks failed. Please review the output above." "Warning"
    Write-Status "`n💡 Next steps:" "Info"
    if (-not $formatSuccess) {
        Write-Host "  1. Review formatting errors and fix manually if needed"
    }
    if (-not $lintSuccess) {
        Write-Host "  2. Review linting errors and fix the issues"
    }
    if (-not $typeSuccess) {
        Write-Host "  3. Review type checking errors and add type annotations"
        Write-Host "     💡 Use 'scripts/type_check.ps1 -Baseline' to regenerate baseline"
    }
    Write-Host "  4. Re-run this script to verify fixes"
}

exit $(if ($overallSuccess) { 0 } else { 1 })
