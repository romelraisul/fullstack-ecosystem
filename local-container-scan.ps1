# Local Container Security Scanner
# Mimics the GitHub Actions workflow locally

param(
    [string]$Images = "nginx:latest,alpine:3.18",
    [string]$OutputDir = "./scan-results"
)

Write-Host "Starting local container security scan..." -ForegroundColor Green
Write-Host "Images to scan: $Images" -ForegroundColor Yellow

# Tool paths (adjust if tools are installed elsewhere)
$TrivyPath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\AquaSecurity.Trivy_Microsoft.Winget.Source_8wekyb3d8bbwe\trivy.exe"
$GrypePath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\Anchore.Grype_Microsoft.Winget.Source_8wekyb3d8bbwe\grype.exe"
$SyftPath = "C:\Users\$env:USERNAME\AppData\Local\Microsoft\WinGet\Packages\Anchore.Syft_Microsoft.Winget.Source_8wekyb3d8bbwe\syft.exe"

# Create output directory
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force
}

# Split images into array
$ImageList = $Images -split ","

# Initialize results array
$AllResults = @()

foreach ($Image in $ImageList) {
    $Image = $Image.Trim()
    Write-Host "`nScanning image: $Image" -ForegroundColor Cyan

    # Create image-specific directory
    $ImageDir = Join-Path $OutputDir ($Image -replace "[:/]", "_")
    if (!(Test-Path $ImageDir)) {
        New-Item -ItemType Directory -Path $ImageDir -Force
    }

    try {
        # Pull image
        Write-Host "  Pulling image..." -ForegroundColor Gray
        docker pull $Image 2>$null

        # Run Trivy scan
        Write-Host "  Running Trivy scan..." -ForegroundColor Gray
        $TrivyOutput = Join-Path $ImageDir "trivy.json"
        & $TrivyPath image --severity CRITICAL, HIGH, MEDIUM, LOW --format json -o $TrivyOutput $Image 2>$null

        # Run Grype scan
        Write-Host "  Running Grype scan..." -ForegroundColor Gray
        $GrypeOutput = Join-Path $ImageDir "grype.json"
        & $GrypePath $Image -o json > $GrypeOutput 2>$null

        # Run Syft scan
        Write-Host "  Running Syft scan..." -ForegroundColor Gray
        $SyftOutput = Join-Path $ImageDir "syft.json"
        & $SyftPath $Image -o json > $SyftOutput 2>$null

        # Process results and create policy summary
        Write-Host "  Creating policy summary..." -ForegroundColor Gray
        $PolicySummary = Join-Path $ImageDir "policy-summary.json"

        if (Test-Path $TrivyOutput) {
            $TrivyData = Get-Content $TrivyOutput | ConvertFrom-Json
            $Results = @{
                image           = $Image
                trivy           = $TrivyData.Results
                scan_date       = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
                vulnerabilities = @{
                    critical = 0
                    high     = 0
                    medium   = 0
                    low      = 0
                }
            }

            # Count vulnerabilities by severity
            if ($TrivyData.Results) {
                foreach ($result in $TrivyData.Results) {
                    if ($result.Vulnerabilities) {
                        foreach ($vuln in $result.Vulnerabilities) {
                            switch ($vuln.Severity.ToLower()) {
                                "critical" { $Results.vulnerabilities.critical++ }
                                "high" { $Results.vulnerabilities.high++ }
                                "medium" { $Results.vulnerabilities.medium++ }
                                "low" { $Results.vulnerabilities.low++ }
                            }
                        }
                    }
                }
            }

            $Results | ConvertTo-Json -Depth 10 | Out-File $PolicySummary -Encoding UTF8
            $AllResults += $Results

            Write-Host "    Critical: $($Results.vulnerabilities.critical)" -ForegroundColor Red
            Write-Host "    High: $($Results.vulnerabilities.high)" -ForegroundColor Magenta
            Write-Host "    Medium: $($Results.vulnerabilities.medium)" -ForegroundColor Yellow
            Write-Host "    Low: $($Results.vulnerabilities.low)" -ForegroundColor White
        }

    }
    catch {
        Write-Host "  Error scanning $Image`: $_" -ForegroundColor Red
    }
}

# Create combined summary
Write-Host "`nCreating combined policy summary..." -ForegroundColor Green
$CombinedSummary = @{
    scan_date             = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    images                = $AllResults
    total_vulnerabilities = @{
        critical = ($AllResults | ForEach-Object { $_.vulnerabilities.critical } | Measure-Object -Sum).Sum
        high     = ($AllResults | ForEach-Object { $_.vulnerabilities.high } | Measure-Object -Sum).Sum
        medium   = ($AllResults | ForEach-Object { $_.vulnerabilities.medium } | Measure-Object -Sum).Sum
        low      = ($AllResults | ForEach-Object { $_.vulnerabilities.low } | Measure-Object -Sum).Sum
    }
    overall_pass          = $true  # Customize this logic based on your policy
}

$CombinedOutputPath = Join-Path $OutputDir "combined-policy-summary.json"
$CombinedSummary | ConvertTo-Json -Depth 10 | Out-File $CombinedOutputPath -Encoding UTF8

# Create markdown summary
$MarkdownPath = Join-Path $OutputDir "scan-summary.md"
$Markdown = @"
# Container Security Scan Results

**Scan Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Summary
- **Images Scanned:** $($AllResults.Count)
- **Total Critical:** $($CombinedSummary.total_vulnerabilities.critical)
- **Total High:** $($CombinedSummary.total_vulnerabilities.high)
- **Total Medium:** $($CombinedSummary.total_vulnerabilities.medium)
- **Total Low:** $($CombinedSummary.total_vulnerabilities.low)

## Per-Image Results

"@

foreach ($result in $AllResults) {
    $Markdown += @"

### $($result.image)
- Critical: $($result.vulnerabilities.critical)
- High: $($result.vulnerabilities.high)
- Medium: $($result.vulnerabilities.medium)
- Low: $($result.vulnerabilities.low)

"@
}

$Markdown | Out-File $MarkdownPath -Encoding UTF8

Write-Host "`nScan completed!" -ForegroundColor Green
Write-Host "Results saved to: $OutputDir" -ForegroundColor Yellow
Write-Host "Combined summary: $CombinedOutputPath" -ForegroundColor Yellow
Write-Host "Markdown report: $MarkdownPath" -ForegroundColor Yellow
