# Local Container Security Scanning

This directory contains scripts to run container security scans locally, mimicking the GitHub Actions workflows without requiring GitHub.

## Prerequisites

Install the required security scanning tools:

```powershell
# Install Trivy
winget install aquasec.trivy

# Install Grype
winget install anchore.grype

# Install Syft
winget install anchore.syft

# Verify installations
trivy --version
grype version
syft version
```

## Usage

### PowerShell (Windows)

```powershell
# Scan default images (nginx:latest, alpine:3.18)
.\local-container-scan.ps1

# Scan custom images
.\local-container-scan.ps1 -Images "ubuntu:22.04,python:3.11-slim" -OutputDir "./custom-scan"

# Scan single image
.\local-container-scan.ps1 -Images "redis:alpine"
```

### Bash (Linux/macOS/WSL)

```bash
# Make script executable
chmod +x local-container-scan.sh

# Scan default images
./local-container-scan.sh

# Scan custom images
./local-container-scan.sh "ubuntu:22.04,python:3.11-slim" "./custom-scan"

# Scan single image
./local-container-scan.sh "redis:alpine"
```

## Output

The scripts generate:

- `scan-results/` - Directory containing all scan results
- `scan-results/[image-name]/` - Per-image directories with:
  - `trivy.json` - Trivy vulnerability scan results
  - `grype.json` - Grype vulnerability scan results
  - `syft.json` - Syft SBOM (Software Bill of Materials)
  - `policy-summary.json` - Processed vulnerability summary
- `scan-results/combined-policy-summary.json` - Aggregated results from all images
- `scan-results/scan-summary.md` - Human-readable markdown report

## Example Output

```
Starting local container security scan...
Images to scan: nginx:latest,alpine:3.18

Scanning image: nginx:latest
  Pulling image...
  Running Trivy scan...
  Running Grype scan...
  Running Syft scan...
  Creating policy summary...
    Critical: 0
    High: 2
    Medium: 8
    Low: 15

Scanning image: alpine:3.18
  Pulling image...
  Running Trivy scan...
  Running Grype scan...
  Running Syft scan...
  Creating policy summary...
    Critical: 0
    High: 0
    Medium: 1
    Low: 3

Creating combined policy summary...

Scan completed!
Results saved to: ./scan-results
Combined summary: ./scan-results/combined-policy-summary.json
Markdown report: ./scan-results/scan-summary.md
```

## Customization

You can modify the scripts to:

- Add custom policy logic for pass/fail decisions
- Change vulnerability severity thresholds
- Add additional scanners or analysis tools
- Customize output formats
- Integrate with other security tools

## GitHub Actions Equivalent

These local scripts replicate the functionality of:

- `container-security-reusable.yml` - Matrix scanning with per-image results
- `container-security-matrix.yml` - Multi-image scanning and aggregation

The local scripts provide the same scanning capabilities without requiring GitHub Actions infrastructure.
