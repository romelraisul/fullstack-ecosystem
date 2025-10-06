# Pre-commit setup script for PowerShell
param(
    [switch]$Help,
    [switch]$Test,
    [switch]$SkipTest
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
Pre-commit Setup Script

Usage: .\scripts\setup_pre_commit.ps1 [options]

Options:
  -Help         Show this help message
  -Test         Run pre-commit test after setup
  -SkipTest     Skip the pre-commit test

Examples:
  .\scripts\setup_pre_commit.ps1           # Full setup with test
  .\scripts\setup_pre_commit.ps1 -SkipTest # Setup without test
  .\scripts\setup_pre_commit.ps1 -Test     # Just run test
"@
    exit 0
}

Write-Status "🚀 Setting up pre-commit hooks for fullstack-ecosystem" "Info"
Write-Host "=" * 60

# Check if we're in the right directory
if (-not (Test-Path ".pre-commit-config.yaml")) {
    Write-Status "❌ .pre-commit-config.yaml not found!" "Error"
    Write-Status "Please run this script from the project root directory." "Error"
    exit 1
}

# Check dependencies
Write-Status "🔍 Checking dependencies..." "Info"
$requiredPackages = @("pre-commit", "pytest", "black", "ruff", "mypy", "flake8")
$missing = @()

foreach ($package in $requiredPackages) {
    $packageName = $package -replace "-", "_"
    try {
        $null = python -c "import $packageName" 2>$null
        Write-Status "✅ $package is installed" "Success"
    }
    catch {
        $missing += $package
        Write-Status "❌ $package is missing" "Error"
    }
}

if ($missing.Count -gt 0) {
    Write-Status "⚠️  Missing packages: $($missing -join ', ')" "Warning"
    Write-Status "Install them with: pip install $($missing -join ' ')" "Info"
    exit 1
}

Write-Status "✅ All required dependencies are installed" "Success"

# Setup pre-commit (if not just testing)
if (-not $Test) {
    Write-Status "🎯 Setting up pre-commit hooks..." "Info"

    $commands = @(
        @{cmd = "python -m pre_commit install"; desc = "Installing pre-commit hooks" },
        @{cmd = "python -m pre_commit install --hook-type pre-push"; desc = "Installing pre-push hooks" },
        @{cmd = "python -m pre_commit autoupdate"; desc = "Updating hook versions" }
    )

    $allSuccess = $true
    foreach ($command in $commands) {
        Write-Status "🔧 $($command.desc)..." "Info"
        try {
            $output = Invoke-Expression $command.cmd 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "✅ $($command.desc) completed successfully" "Success"
                if ($output) { Write-Host $output }
            }
            else {
                Write-Status "❌ $($command.desc) failed" "Error"
                if ($output) { Write-Host $output }
                $allSuccess = $false
            }
        }
        catch {
            Write-Status "❌ $($command.desc) failed: $($_.Exception.Message)" "Error"
            $allSuccess = $false
        }
    }

    if (-not $allSuccess) {
        Write-Status "❌ Pre-commit setup failed" "Error"
        exit 1
    }
}

# Test pre-commit (unless skipped)
if (-not $SkipTest) {
    Write-Status "🧪 Testing pre-commit installation..." "Info"

    # Find a Python file to test with
    $testFiles = @("scripts/format.py", "scripts/lint.py", "scripts/type_check.py")
    $testFile = $null

    foreach ($file in $testFiles) {
        if (Test-Path $file) {
            $testFile = $file
            break
        }
    }

    if (-not $testFile) {
        Write-Status "⚠️  No test files found, skipping pre-commit test" "Warning"
    }
    else {
        Write-Status "Testing with file: $testFile" "Info"
        try {
            $output = python -m pre_commit run --files $testFile 2>&1
            Write-Status "Pre-commit test output:" "Info"
            Write-Host $output
            Write-Status "✅ Pre-commit test completed (check output above for any issues)" "Success"
        }
        catch {
            Write-Status "⚠️  Pre-commit test encountered an issue: $($_.Exception.Message)" "Warning"
        }
    }
}

# Success summary
Write-Host "`n" + "=" * 60
Write-Status "🎉 Pre-commit setup completed!" "Success"

Write-Host "`n📋 What's been configured:"
Write-Host "  • Code formatting (black + ruff format)"
Write-Host "  • Code linting (ruff + flake8)"
Write-Host "  • Type checking (mypy)"
Write-Host "  • Fast tests (pytest unit tests)"
Write-Host "  • File validation (trailing whitespace, yaml, json, etc.)"
Write-Host "  • Security scanning (bandit)"

Write-Host "`n💡 Usage:"
Write-Host "  • Hooks run automatically on git commit"
Write-Host "  • Full quality check runs on git push"
Write-Host "  • Manual run: pre-commit run --all-files"
Write-Host "  • Skip hooks: git commit --no-verify"

Write-Host "`n🔧 Management commands:"
Write-Host "  • make pre-commit-install  # Reinstall hooks"
Write-Host "  • make pre-commit-run      # Run on all files"
Write-Host "  • make pre-commit-update   # Update hook versions"

Write-Status "Ready to commit with confidence! 🚀" "Success"
