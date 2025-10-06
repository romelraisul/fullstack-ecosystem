# Code formatting script using Black and Ruff for PowerShell
param(
    [switch]$Help,
    [string[]]$Targets = @("autogen", "tests", "scripts", "*.py")
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

    Write-Status "`n🔧 $Description..." "Info"
    try {
        $output = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ $Description completed successfully" "Success"
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
Code Formatting Script

Usage: .\scripts\format.ps1 [options]

Options:
  -Help           Show this help message
  -Targets        Specify custom targets (default: autogen, tests, scripts, *.py)

Examples:
  .\scripts\format.ps1                    # Format default targets
  .\scripts\format.ps1 -Targets autogen  # Format only autogen directory
"@
    exit 0
}

Write-Status "🎨 Running code formatting..." "Info"

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
    Write-Status "❌ No Python files found to format" "Error"
    exit 1
}

$targetsString = $targetList -join " "
Write-Status "Formatting targets: $targetsString" "Info"

$success = $true

# Run ruff format (modern formatter)
if (-not (Invoke-SafeCommand "ruff format $targetsString" "Ruff formatting")) {
    $success = $false
}

# Run ruff --fix for auto-fixable issues
if (-not (Invoke-SafeCommand "ruff check --fix $targetsString" "Ruff auto-fixes")) {
    $success = $false
}

# Run black as backup/alternative
if (-not (Invoke-SafeCommand "black $targetsString" "Black formatting")) {
    $success = $false
}

if ($success) {
    Write-Status "`n🎉 All formatting completed successfully!" "Success"
}
else {
    Write-Status "`n⚠️ Some formatting steps failed. Please check the output above." "Warning"
}

exit $(if ($success) { 0 } else { 1 })
