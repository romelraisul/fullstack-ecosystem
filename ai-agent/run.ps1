param(
    [ValidateSet('agent','evaluate')]
    [string]$Mode = 'agent',
    [string]$GithubToken,
    [string]$FoundryEndpoint,
    [string]$FoundryKey,
    [switch]$Bootstrap
)

Write-Host "Hybrid Cloud Infrastructure Agent Runner" -ForegroundColor Cyan

# 1. Resolve Python interpreter (prefer workspace venv)
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$venvDir = Join-Path $workspaceRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$systemPythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pyLauncherCmd = Get-Command py -ErrorAction SilentlyContinue

if ($Bootstrap -and -not (Test-Path $venvPython)) {
    Write-Host "Bootstrapping venv at $venvDir" -ForegroundColor Yellow
    if ($pyLauncherCmd) {
        & $pyLauncherCmd.Source -3 -m venv $venvDir
    } elseif ($systemPythonCmd) {
        & $systemPythonCmd.Source -m venv $venvDir
    } else {
        Write-Error "No Python launcher found. Install Python 3.12 via winget: winget install Python.Python.3.12"
        exit 1
    }
}

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "Using venv Python: $pythonExe" -ForegroundColor Yellow
} else {
    if (-not $systemPythonCmd) {
        Write-Error "Python is not installed or not in PATH. Install Python 3.12 via winget: winget install Python.Python.3.12"
        exit 1
    }
    $pythonExe = $systemPythonCmd.Source
    Write-Host "Using system Python: $pythonExe" -ForegroundColor Yellow
}

# 2. Verify dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip show agent-framework-azure-ai | Out-Null
if ($LASTEXITCODE -ne 0 -or $Bootstrap) {
    Write-Host "Installing requirements (preview packages)..." -ForegroundColor Yellow
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install --pre -r "$PSScriptRoot\requirements.txt"
}


# 3. Set Foundry (Azure) credentials if provided
if ($FoundryEndpoint) {
    $env:AZURE_OPENAI_ENDPOINT = $FoundryEndpoint
}
if ($FoundryKey) {
    $env:AZURE_OPENAI_KEY = $FoundryKey
}

# Print the active model configuration that will be used by the Python scripts
$foundryEndpointEnv = $env:AZURE_OPENAI_ENDPOINT
$foundryKeyEnv = $env:AZURE_OPENAI_KEY
$foundryModelEnv = $env:AZURE_OPENAI_MODEL
$githubTokenEnv = $env:GITHUB_TOKEN

if ($foundryEndpointEnv -and $foundryKeyEnv) {
    if (-not $foundryModelEnv) { $foundryModelEnv = 'gpt-4o-mini' }
    Write-Host "Model source: Foundry (Azure) - model='$foundryModelEnv' endpoint='$foundryEndpointEnv'" -ForegroundColor Cyan
} elseif ($githubTokenEnv) {
    Write-Host "Model source: GitHub Models - model='gpt-4o-mini' endpoint='https://models.github.ai/inference'" -ForegroundColor Cyan
} else {
    Write-Warning "No model credentials detected: set AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_KEY or GITHUB_TOKEN in environment."
}

# 4. Check if AI Toolkit Trace Viewer (OTLP collector) is reachable
Write-Host "Checking trace collector at http://localhost:4318..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4318" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Trace collector is reachable." -ForegroundColor Green
} catch {
    Write-Warning "Trace collector not reachable."
    Write-Host "Open VS Code, run 'AI Toolkit: Open Trace Viewer' to start the collector (OTLP at http://localhost:4318)." -ForegroundColor Yellow
}

# 5. Run agent or evaluation
switch ($Mode) {
    'evaluate' {
        Write-Host "Running evaluation..." -ForegroundColor Green
        & $pythonExe "$PSScriptRoot\evaluate_agent.py"
    }
    default {
        Write-Host "Starting agent..." -ForegroundColor Green
        & $pythonExe "$PSScriptRoot\infrastructure_agent.py"
    }
}
