<#
.SYNOPSIS
  Build a full ML/LLM capable onedir PyInstaller distribution of the advanced backend.

.DESCRIPTION
  Automates environment creation (venv_full), dependency installation, and PyInstaller invocation
  with all heavy ML/LLM libraries. TensorFlow is OPTIONAL (huge footprint) and only included
  when -IncludeTensorFlow is passed or INCLUDE_TENSORFLOW=1 environment variable is set.

.PARAMETER Clean
  Remove previous dist/build/spec artifacts before building.

.PARAMETER IncludeTensorFlow
  Include TensorFlow in dependency install & hidden-import list.

.PARAMETER Name
  Base name for the built distribution (default: advanced_backend_full_onedir)

.PARAMETER Python
  Path to python executable to use (default: tries current session, else searches venv_full).

.EXAMPLE
  ./scripts/package_full_ml.ps1 -Clean

.EXAMPLE
  ./scripts/package_full_ml.ps1 -IncludeTensorFlow -Name backend_full_tf

.NOTES
  Run from repository root. Produces dist/<Name>/<Name>.exe
#>
[CmdletBinding()] param(
    [switch] $Clean,
    [switch] $IncludeTensorFlow,
    [string] $Name = 'advanced_backend_full_onedir',
    [string] $Python
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $repoRoot

# Resolve python
if (-not $Python) {
    if (Test-Path "$repoRoot\venv_full\Scripts\python.exe") { $Python = "$repoRoot\venv_full\Scripts\python.exe" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = (Get-Command python).Source }
    else { throw 'Python interpreter not found. Provide -Python path or create venv_full.' }
}

Write-Info "Using Python: $Python"

# Create venv_full if missing
if (-not (Test-Path "$repoRoot\venv_full")) {
    Write-Info 'Creating venv_full virtual environment'
    & $Python -m venv venv_full
    $Python = "$repoRoot\venv_full\Scripts\python.exe"
}

# Upgrade pip
& $Python -m pip install --upgrade pip > $null

# Install core deps (minimal list + heavy libs)
$baseReq = @(
    'fastapi', 'uvicorn', 'pydantic', 'python-multipart', 'tdigest', 'prometheus_client', 'passlib', 'bcrypt', 'python-magic-bin'
)
$mlReq = @('torch', 'scikit-learn', 'langchain', 'openai', 'anthropic', 'tiktoken', 'transformers')
if ($IncludeTensorFlow -or $env:INCLUDE_TENSORFLOW -in @('1', 'true', 'on')) { $mlReq += 'tensorflow'; Write-Warn 'Including TensorFlow (large download).' }

Write-Info 'Installing dependencies...'
& $Python -m pip install --quiet --upgrade @baseReq @mlReq PyJWT pyinstaller | Out-Null

# Optional clean
if ($Clean) {
    Write-Info 'Cleaning previous build artifacts'
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, "$Name.spec"
}

$hidden = @(
    'accumulation_tree', 'torch', 'sklearn', 'langchain', 'openai', 'anthropic', 'tiktoken', 'transformers', 'jwt', 'magic'
)
if (-not ($IncludeTensorFlow -or $env:INCLUDE_TENSORFLOW -in @('1', 'true', 'on'))) {
    Write-Info 'TensorFlow omitted (use -IncludeTensorFlow to add)'
}
else {
    $hidden += 'tensorflow'
}

$hiddenArgs = $hidden | ForEach-Object { "--hidden-import $_" }

Write-Info 'Invoking PyInstaller (onedir)...'
$cmd = @(
    'pyinstaller', 'bootstrap_entry.py', '--noconfirm', '--name', $Name,
    '--add-data', 'executive_dashboard.html;.'
) + $hiddenArgs

Write-Host "[CMD] $($cmd -join ' ')" -ForegroundColor DarkGray
& $Python $cmd

if ($LASTEXITCODE -ne 0) { Write-Err "PyInstaller failed with code $LASTEXITCODE"; exit $LASTEXITCODE }

$exePath = Join-Path "$repoRoot\dist" $Name | Join-Path -ChildPath $Name | Join-Path -ChildPath ("$Name.exe")
if (-not (Test-Path $exePath)) {
    # Some PyInstaller versions put exe directly under dist/<Name>/
    $alt = Join-Path "$repoRoot\dist" $Name | Join-Path -ChildPath ("$Name.exe")
    if (Test-Path $alt) { $exePath = $alt }
}

if (Test-Path $exePath) {
    $sizeMB = [Math]::Round((Get-Item $exePath).Length / 1MB, 2)
    Write-Info "Build complete: $exePath (${sizeMB}MB)"
    Write-Info "Run example: `n  $env:MINIMAL_MODE=0; $exePath"
    Write-Info 'Hit http://localhost:8000/ml-capabilities after startup.'
}
else {
    Write-Warn 'Executable not found where expected.'
}
