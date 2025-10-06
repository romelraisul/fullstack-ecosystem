param(
    [Parameter(Position = 0)] [string]$TestProfile = "fast",
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'

function Invoke-PyTests([string[]]$PyTestArgs) {
    if ($Verbose) { Write-Host "Running: python -m pytest $PyTestArgs" -ForegroundColor Cyan }
    python -m pytest @PyTestArgs
}

switch ($TestProfile.ToLower()) {
    'fast' { Invoke-PyTests @() }
    'slow' { Invoke-PyTests -PyTestArgs @('-m', 'slow') }
    'integration' { Invoke-PyTests -PyTestArgs @('-m', 'integration') }
    'all' { Invoke-PyTests -PyTestArgs @('-m', 'slow or integration or not slow') }
    'scripts' { Invoke-PyTests -PyTestArgs @('tests/scripts', '-q') }
    default { Write-Error "Unknown profile '$TestProfile'. Use fast|slow|integration|all|scripts" }
}
