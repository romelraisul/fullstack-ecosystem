#!/usr/bin/env bash
"""Enhanced SBOM generation and deep analysis integration.

This script combines SBOM generation with deep analysis capabilities,
integrating with existing CI/CD workflows and security scanners.
"""

# Enhanced SBOM Generation and Analysis Configuration
SBOM_CONFIG_FILE="sbom-analysis-config.yaml"
ANALYSIS_OUTPUT_DIR="sbom-analysis-output"
DEFAULT_FORMATS=("cyclonedx" "spdx" "syft-json")

# Create configuration file
cat > "${SBOM_CONFIG_FILE}" << 'EOF'
# Deep SBOM Analysis Configuration
sbom_generation:
  formats:
    - cyclonedx
    - spdx
    - syft-json

  output_directory: "sbom-analysis-output"

  # Syft configuration
  syft:
    scope: "all-layers"
    output_formats: ["json", "cyclonedx-json", "spdx-json"]

  # Trivy SBOM configuration
  trivy:
    enable_secret_scanning: true
    enable_license_scanning: true

vulnerability_analysis:
  databases:
    trivy: true
    grype: true
    osv: true

  severity_threshold: "medium"

  # Retry configuration for flaky network connections
  retry:
    max_attempts: 3
    backoff_factor: 2

supply_chain_analysis:
  enable_typosquatting_detection: true
  enable_suspicious_version_detection: true
  enable_supplier_verification: true

license_analysis:
  enable_compliance_checking: true
  high_risk_licenses:
    - "GPL-2.0"
    - "GPL-3.0"
    - "AGPL-1.0"
    - "AGPL-3.0"

reporting:
  formats: ["json", "html", "markdown"]
  include_remediation_advice: true

integration:
  github_actions: true
  sarif_output: true
  security_tab_integration: true
EOF

echo "📋 Enhanced SBOM Analysis Configuration Created"

# Create analysis output directory
mkdir -p "${ANALYSIS_OUTPUT_DIR}"

# Function to generate comprehensive SBOM
generate_comprehensive_sbom() {
    local target_path="${1:-.}"
    local project_name="${2:-$(basename "$PWD")}"

    echo "🔍 Generating comprehensive SBOM for: ${project_name}"

    # Generate Syft SBOM in multiple formats
    echo "  📊 Generating Syft SBOM..."
    syft "${target_path}" \
        --output json="${ANALYSIS_OUTPUT_DIR}/${project_name}-syft.json" \
        --output cyclonedx-json="${ANALYSIS_OUTPUT_DIR}/${project_name}-cyclonedx.json" \
        --output spdx-json="${ANALYSIS_OUTPUT_DIR}/${project_name}-spdx.json" \
        --scope all-layers

    # Generate Trivy SBOM with additional metadata
    echo "  🔒 Generating Trivy SBOM..."
    trivy fs "${target_path}" \
        --format cyclonedx \
        --output "${ANALYSIS_OUTPUT_DIR}/${project_name}-trivy-cyclonedx.json" \
        --include-dev-deps

    # Generate container SBOM if Dockerfile exists
    if [[ -f "${target_path}/Dockerfile" ]]; then
        echo "  🐳 Generating container SBOM..."

        # Build temporary image for SBOM generation
        local temp_image="${project_name}-sbom:latest"
        docker build -t "${temp_image}" "${target_path}" || {
            echo "⚠️  Container build failed, skipping container SBOM"
            return 0
        }

        # Generate container SBOM
        syft "${temp_image}" \
            --output json="${ANALYSIS_OUTPUT_DIR}/${project_name}-container-syft.json" \
            --output cyclonedx-json="${ANALYSIS_OUTPUT_DIR}/${project_name}-container-cyclonedx.json"

        trivy image "${temp_image}" \
            --format cyclonedx \
            --output "${ANALYSIS_OUTPUT_DIR}/${project_name}-container-trivy.json"

        # Clean up temporary image
        docker rmi "${temp_image}" || true
    fi

    echo "✅ SBOM generation complete"
}

# Function to perform deep analysis on generated SBOMs
perform_deep_analysis() {
    local project_name="${1:-$(basename "$PWD")}"

    echo "🔬 Performing deep SBOM analysis..."

    # Find generated SBOM files
    local cyclone_dx_file="${ANALYSIS_OUTPUT_DIR}/${project_name}-cyclonedx.json"
    local spdx_file="${ANALYSIS_OUTPUT_DIR}/${project_name}-spdx.json"
    local syft_file="${ANALYSIS_OUTPUT_DIR}/${project_name}-syft.json"

    # Perform analysis on each available SBOM format
    for sbom_file in "${cyclone_dx_file}" "${spdx_file}" "${syft_file}"; do
        if [[ -f "${sbom_file}" ]]; then
            local format=""
            local output_suffix=""

            case "${sbom_file}" in
                *cyclonedx*)
                    format="cyclonedx"
                    output_suffix="cyclonedx"
                    ;;
                *spdx*)
                    format="spdx"
                    output_suffix="spdx"
                    ;;
                *syft*)
                    format="syft-json"
                    output_suffix="syft"
                    ;;
            esac

            echo "  📈 Analyzing ${format} SBOM..."

            # Run deep analysis
            python scripts/deep_sbom_integration.py \
                --input "${sbom_file}" \
                --format "${format}" \
                --output "${ANALYSIS_OUTPUT_DIR}/${project_name}-analysis-${output_suffix}.json" \
                --analyze-dependencies \
                --verbose

            # Generate HTML report
            python -c "
import json
import sys
from pathlib import Path

# Load analysis results
analysis_file = '${ANALYSIS_OUTPUT_DIR}/${project_name}-analysis-${output_suffix}.json'
with open(analysis_file, 'r') as f:
    data = json.load(f)

# Generate HTML report
html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>SBOM Security Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 5px; }
        .score { font-size: 24px; font-weight: bold; color: #2e7d32; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .vulnerability { padding: 10px; margin: 5px 0; border-left: 4px solid #ff5722; background: #ffebee; }
        .risk-high { border-left-color: #d32f2f; }
        .risk-medium { border-left-color: #f57c00; }
        .risk-low { border-left-color: #388e3c; }
    </style>
</head>
<body>
    <div class=\"header\">
        <h1>SBOM Security Analysis Report</h1>
        <div class=\"score\">Security Score: {score}/100</div>
        <p>Analysis Date: {date}</p>
    </div>

    <div class=\"section\">
        <h2>Summary</h2>
        <ul>
            <li>Total Components: {components}</li>
            <li>Vulnerabilities Found: {vulns}</li>
            <li>Critical Issues: {critical}</li>
            <li>Supply Chain Risks: {risks}</li>
        </ul>
    </div>

    <div class=\"section\">
        <h2>Vulnerabilities</h2>
        {vulnerability_list}
    </div>

    <div class=\"section\">
        <h2>Supply Chain Risks</h2>
        {risk_list}
    </div>
</body>
</html>
'''.format(
    score=data['summary']['security_score'],
    date=data['analysis_result']['analysis_metadata']['analysis_date'],
    components=data['summary']['total_components'],
    vulns=data['summary']['total_vulnerabilities'],
    critical=data['summary']['critical_vulnerabilities'],
    risks=len(data['analysis_result']['supply_chain_risks']),
    vulnerability_list='<br>'.join([f'<div class=\"vulnerability\">{v[\"id\"]}: {v[\"description\"][:100]}...</div>' for v in data['analysis_result']['vulnerabilities'][:10]]),
    risk_list='<br>'.join([f'<div class=\"vulnerability risk-{r[\"risk_level\"]}\">{r[\"component\"]}: {r[\"risk_factors\"][0] if r[\"risk_factors\"] else \"Unknown risk\"}</div>' for r in data['analysis_result']['supply_chain_risks'][:10]])
)

# Write HTML report
html_file = '${ANALYSIS_OUTPUT_DIR}/${project_name}-report-${output_suffix}.html'
with open(html_file, 'w') as f:
    f.write(html_content)

print(f'HTML report generated: {html_file}')
"

        fi
    done

    echo "✅ Deep analysis complete"
}

# Function to integrate with GitHub Actions
generate_github_action_integration() {
    local workflow_file=".github/workflows/deep-sbom-analysis.yml"

    mkdir -p "$(dirname "${workflow_file}")"

    cat > "${workflow_file}" << 'EOF'
name: Deep SBOM Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Mondays at 2 AM

env:
  ANALYSIS_OUTPUT_DIR: sbom-analysis-output

jobs:
  deep-sbom-analysis:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      security-events: write
      actions: read

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install security tools
      run: |
        # Install Syft
        curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

        # Install Grype
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

        # Install Trivy
        sudo apt-get update
        sudo apt-get install wget apt-transport-https gnupg lsb-release
        wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
        echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
        sudo apt-get update
        sudo apt-get install trivy

    - name: Create output directory
      run: mkdir -p ${{ env.ANALYSIS_OUTPUT_DIR }}

    - name: Generate comprehensive SBOM
      run: |
        PROJECT_NAME="${{ github.event.repository.name }}"

        # Generate Syft SBOM in multiple formats
        syft . \
          --output json="${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-syft.json" \
          --output cyclonedx-json="${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-cyclonedx.json" \
          --output spdx-json="${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-spdx.json" \
          --scope all-layers

        # Generate Trivy SBOM
        trivy fs . \
          --format cyclonedx \
          --output "${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-trivy-cyclonedx.json"

    - name: Perform deep SBOM analysis
      run: |
        PROJECT_NAME="${{ github.event.repository.name }}"

        # Install Python dependencies for analysis
        pip install requests urllib3

        # Analyze CycloneDX SBOM
        python scripts/deep_sbom_integration.py \
          --input "${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-cyclonedx.json" \
          --format cyclonedx \
          --output "${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-analysis.json" \
          --analyze-dependencies \
          --verbose

    - name: Generate SARIF output for GitHub Security tab
      run: |
        PROJECT_NAME="${{ github.event.repository.name }}"

        # Convert analysis results to SARIF format
        python -c "
import json
from datetime import datetime, UTC

# Load analysis results
with open('${{ env.ANALYSIS_OUTPUT_DIR }}/${PROJECT_NAME}-analysis.json', 'r') as f:
    analysis_data = json.load(f)

# Generate SARIF report
sarif_report = {
    'version': '2.1.0',
    '\$schema': 'https://json.schemastore.org/sarif-2.1.0.json',
    'runs': [{
        'tool': {
            'driver': {
                'name': 'Deep SBOM Analysis',
                'version': '1.0.0',
                'informationUri': 'https://github.com/your-org/deep-sbom-analysis'
            }
        },
        'results': []
    }]
}

# Add vulnerability results
for vuln in analysis_data['analysis_result']['vulnerabilities'][:50]:  # Limit for GitHub
    result = {
        'ruleId': vuln['id'],
        'level': 'error' if vuln['severity'].lower() in ['critical', 'high'] else 'warning',
        'message': {
            'text': f\"{vuln['id']}: {vuln['description'][:100]}...\"
        },
        'locations': [{
            'physicalLocation': {
                'artifactLocation': {
                    'uri': 'sbom-analysis'
                },
                'region': {
                    'startLine': 1,
                    'startColumn': 1
                }
            }
        }],
        'properties': {
            'component': vuln['component'],
            'version': vuln['version'],
            'severity': vuln['severity'],
            'score': vuln['score']
        }
    }
    sarif_report['runs'][0]['results'].append(result)

# Write SARIF report
with open('${{ env.ANALYSIS_OUTPUT_DIR }}/deep-sbom-analysis.sarif', 'w') as f:
    json.dump(sarif_report, f, indent=2)
"

    - name: Upload SARIF to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: ${{ env.ANALYSIS_OUTPUT_DIR }}/deep-sbom-analysis.sarif
        category: deep-sbom-analysis

    - name: Upload analysis artifacts
      uses: actions/upload-artifact@v3
      with:
        name: sbom-analysis-results
        path: ${{ env.ANALYSIS_OUTPUT_DIR }}/
        retention-days: 30

    - name: Comment PR with analysis summary
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const analysisFile = '${{ env.ANALYSIS_OUTPUT_DIR }}/${{ github.event.repository.name }}-analysis.json';

          if (fs.existsSync(analysisFile)) {
            const analysis = JSON.parse(fs.readFileSync(analysisFile, 'utf8'));
            const summary = analysis.summary;

            const comment = `## 🔍 Deep SBOM Analysis Results

**Security Score:** ${summary.security_score}/100
**Components Analyzed:** ${summary.total_components}
**Vulnerabilities Found:** ${summary.total_vulnerabilities}
**Critical Issues:** ${summary.critical_vulnerabilities}
**High-Risk Components:** ${summary.high_risk_components}
**License Compliance:** ${summary.license_compliance_score}/100

${summary.critical_vulnerabilities > 0 ? '⚠️ **Critical vulnerabilities found!** Please review the security analysis.' : '✅ No critical vulnerabilities detected.'}

[View detailed analysis artifacts](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
          }
EOF

    echo "📋 GitHub Actions workflow created: ${workflow_file}"
}

# Function to create comprehensive documentation
create_documentation() {
    local doc_file="docs/DEEP_SBOM_ANALYSIS.md"

    mkdir -p "$(dirname "${doc_file}")"

    cat > "${doc_file}" << 'EOF'
# Deep SBOM Analysis Integration

This document describes the comprehensive Software Bill of Materials (SBOM) analysis and security integration implemented in this project.

## Overview

The deep SBOM analysis system provides:

- **Multi-format SBOM generation** (CycloneDX, SPDX, Syft JSON)
- **Comprehensive vulnerability scanning** (Trivy, Grype, OSV)
- **Supply chain security assessment**
- **License compliance analysis**
- **Dependency tree analysis**
- **GitHub Security tab integration**

## Components

### 1. SBOM Generation

The system generates SBOMs in multiple formats to ensure compatibility:

- **CycloneDX**: Industry standard for security-focused SBOM
- **SPDX**: Linux Foundation standard for license compliance
- **Syft JSON**: Anchore's native format with rich metadata

### 2. Deep Security Analysis

#### Vulnerability Detection
- Cross-references multiple vulnerability databases
- Correlates findings across different scanners
- Provides severity scoring and remediation advice

#### Supply Chain Analysis
- Detects potential typosquatting attacks
- Identifies suspicious version patterns
- Verifies component supplier authenticity
- Assesses integrity verification status

#### License Compliance
- Analyzes license compatibility and risks
- Identifies high-risk copyleft licenses
- Provides compliance recommendations

### 3. Integration Points

#### GitHub Actions
- Automated analysis on every push/PR
- SARIF output for Security tab integration
- Artifact upload for historical tracking
- PR comments with analysis summary

#### Container Security
- Integrates with existing container scanning workflows
- Generates container-specific SBOMs
- Correlates vulnerabilities across layers

## Usage

### Manual Analysis

```bash
# Generate comprehensive SBOM
./scripts/enhanced-sbom-generation.sh

# Perform deep analysis
python scripts/deep_sbom_integration.py \
  --input sbom-analysis-output/project-cyclonedx.json \
  --format cyclonedx \
  --output analysis-results.json \
  --analyze-dependencies
```

### GitHub Actions Integration

The system automatically runs on:
- Push to main/develop branches
- Pull requests
- Weekly scheduled scans

Results are available in:
- GitHub Security tab (SARIF upload)
- Action artifacts (detailed reports)
- PR comments (summary)

### Configuration

Edit `sbom-analysis-config.yaml` to customize:

```yaml
vulnerability_analysis:
  severity_threshold: "medium"
  databases:
    trivy: true
    grype: true
    osv: true

supply_chain_analysis:
  enable_typosquatting_detection: true
  enable_suspicious_version_detection: true

license_analysis:
  high_risk_licenses:
    - "GPL-2.0"
    - "AGPL-3.0"
```

## Analysis Output

### JSON Report Structure

```json
{
  "analysis_result": {
    "components": [...],
    "vulnerabilities": [...],
    "supply_chain_risks": [...],
    "license_analysis": {...},
    "security_score": 85.2
  },
  "summary": {
    "security_score": 85.2,
    "total_components": 156,
    "total_vulnerabilities": 8,
    "critical_vulnerabilities": 0,
    "high_risk_components": 2
  }
}
```

### HTML Report

Interactive HTML reports include:
- Executive summary with security score
- Vulnerability details with remediation advice
- Supply chain risk assessment
- License compliance analysis
- Component inventory

## Security Score Calculation

The security score (0-100, higher is better) considers:

- **Vulnerability severity**: Critical (-15), High (-10), Medium (-5), Low (-2)
- **Supply chain risks**: Based on risk factors and patterns
- **License compliance**: Penalty for high-risk licenses
- **Component verification**: Missing hashes, suppliers

## Best Practices

### For Development Teams

1. **Review analysis results** in PR comments before merging
2. **Address critical vulnerabilities** immediately
3. **Monitor supply chain risks** for new components
4. **Verify license compliance** for commercial use

### for Security Teams

1. **Set severity thresholds** appropriate for your risk tolerance
2. **Configure alerts** for critical findings
3. **Review historical trends** using artifact storage
4. **Integrate with existing security tools**

### For DevOps Teams

1. **Customize CI/CD integration** based on deployment patterns
2. **Archive analysis artifacts** for compliance reporting
3. **Monitor analysis performance** and optimize as needed
4. **Update security tools** regularly for latest vulnerability data

## Troubleshooting

### Common Issues

#### Analysis Tool Installation Failures
- Ensure proper permissions for tool installation
- Check network connectivity for downloads
- Verify supported OS/architecture

#### Large SBOM Processing
- Increase timeout values for complex projects
- Consider filtering by component types
- Use parallel processing where available

#### False Positive Vulnerabilities
- Configure allow-lists for known safe components
- Adjust severity thresholds
- Cross-reference with multiple databases

### Performance Optimization

- **Cache vulnerability databases** to reduce scan time
- **Use incremental analysis** for large repositories
- **Parallelize scanning** across multiple formats
- **Filter components** by relevance to reduce noise

## Compliance and Reporting

### Regulatory Requirements

The analysis supports compliance with:
- **NIST Cybersecurity Framework**
- **OWASP Software Component Verification Standard**
- **ISO/IEC 27001** for information security management
- **SOC 2** for service organization controls

### Audit Trail

All analysis results include:
- Timestamp and analyzer version
- Input SBOM fingerprint
- Analysis configuration
- Component and vulnerability counts

## Integration Examples

### GitLab CI/CD

```yaml
sbom_analysis:
  stage: security
  script:
    - ./scripts/enhanced-sbom-generation.sh
    - python scripts/deep_sbom_integration.py --input sbom.json --format cyclonedx
  artifacts:
    reports:
      dependency_scanning: sbom-analysis.json
```

### Jenkins Pipeline

```groovy
stage('SBOM Analysis') {
    steps {
        sh './scripts/enhanced-sbom-generation.sh'
        sh 'python scripts/deep_sbom_integration.py --input sbom.json --format cyclonedx'
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'sbom-analysis-output',
            reportFiles: '*.html',
            reportName: 'SBOM Analysis Report'
        ])
    }
}
```

## Future Enhancements

- **Machine learning** for anomaly detection in dependencies
- **Integration with threat intelligence** feeds
- **Automated remediation** suggestions with patches
- **Real-time monitoring** of component updates
- **Advanced visualization** for dependency relationships

EOF

    echo "📚 Documentation created: ${doc_file}"
}

# Main execution flow
main() {
    echo "🚀 Setting up Deep SBOM Analysis Integration"

    # Ensure scripts directory exists
    mkdir -p scripts

    # Check if deep_sbom_integration.py exists
    if [[ ! -f "scripts/deep_sbom_integration.py" ]]; then
        echo "⚠️  Deep SBOM integration script not found. Please ensure scripts/deep_sbom_integration.py exists."
        return 1
    fi

    # Generate comprehensive SBOM for current project
    generate_comprehensive_sbom "." "$(basename "$PWD")"

    # Perform deep analysis
    perform_deep_analysis "$(basename "$PWD")"

    # Generate GitHub Actions integration
    generate_github_action_integration

    # Create documentation
    create_documentation

    # Summary
    echo ""
    echo "✅ Deep SBOM Analysis Integration Complete!"
    echo ""
    echo "📊 Generated Files:"
    echo "  - SBOM files in ${ANALYSIS_OUTPUT_DIR}/"
    echo "  - Analysis results in ${ANALYSIS_OUTPUT_DIR}/"
    echo "  - GitHub Actions workflow in .github/workflows/"
    echo "  - Documentation in docs/"
    echo ""
    echo "🔍 Next Steps:"
    echo "  1. Review analysis results in ${ANALYSIS_OUTPUT_DIR}/"
    echo "  2. Commit GitHub Actions workflow for automated analysis"
    echo "  3. Configure SBOM analysis thresholds in ${SBOM_CONFIG_FILE}"
    echo "  4. Monitor security scores and vulnerabilities"
    echo ""
    echo "🎯 Security Score: $(python -c "
import json
import glob
import os

analysis_files = glob.glob('${ANALYSIS_OUTPUT_DIR}/*-analysis*.json')
if analysis_files:
    with open(analysis_files[0], 'r') as f:
        data = json.load(f)
    print(f\"{data['summary']['security_score']:.1f}/100\")
else:
    print('Analysis pending...')
")"
}

# Execute main function
main "$@"
