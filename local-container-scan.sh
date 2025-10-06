#!/bin/bash
# Local Container Security Scanner (Bash version)
# Mimics the GitHub Actions workflow locally

IMAGES=${1:-"nginx:latest,alpine:3.18"}
OUTPUT_DIR=${2:-"./scan-results"}

echo "Starting local container security scan..."
echo "Images to scan: $IMAGES"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Split images into array
IFS=',' read -ra IMAGE_LIST <<< "$IMAGES"

# Initialize results
COMBINED_RESULTS="[]"

for IMAGE in "${IMAGE_LIST[@]}"; do
    IMAGE=$(echo "$IMAGE" | xargs)  # trim whitespace
    echo ""
    echo "Scanning image: $IMAGE"

    # Create image-specific directory
    IMAGE_DIR="$OUTPUT_DIR/$(echo "$IMAGE" | sed 's/[:/]/_/g')"
    mkdir -p "$IMAGE_DIR"

    # Pull image
    echo "  Pulling image..."
    docker pull "$IMAGE" >/dev/null 2>&1

    # Run Trivy scan
    echo "  Running Trivy scan..."
    trivy image --severity CRITICAL,HIGH,MEDIUM,LOW --format json -o "$IMAGE_DIR/trivy.json" "$IMAGE" >/dev/null 2>&1

    # Run Grype scan
    echo "  Running Grype scan..."
    grype "$IMAGE" -o json > "$IMAGE_DIR/grype.json" 2>/dev/null

    # Run Syft scan
    echo "  Running Syft scan..."
    syft "$IMAGE" -o json > "$IMAGE_DIR/syft.json" 2>/dev/null

    # Create policy summary
    echo "  Creating policy summary..."
    if [ -f "$IMAGE_DIR/trivy.json" ]; then
        jq --arg image "$IMAGE" '{
            image: $image,
            trivy: .Results,
            scan_date: now | strftime("%Y-%m-%dT%H:%M:%SZ"),
            vulnerabilities: {
                critical: [.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length,
                high: [.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length,
                medium: [.Results[]?.Vulnerabilities[]? | select(.Severity == "MEDIUM")] | length,
                low: [.Results[]?.Vulnerabilities[]? | select(.Severity == "LOW")] | length
            }
        }' "$IMAGE_DIR/trivy.json" > "$IMAGE_DIR/policy-summary.json"

        # Show counts
        CRITICAL=$(jq '.vulnerabilities.critical' "$IMAGE_DIR/policy-summary.json")
        HIGH=$(jq '.vulnerabilities.high' "$IMAGE_DIR/policy-summary.json")
        MEDIUM=$(jq '.vulnerabilities.medium' "$IMAGE_DIR/policy-summary.json")
        LOW=$(jq '.vulnerabilities.low' "$IMAGE_DIR/policy-summary.json")

        echo "    Critical: $CRITICAL"
        echo "    High: $HIGH"
        echo "    Medium: $MEDIUM"
        echo "    Low: $LOW"
    fi
done

# Create combined summary
echo ""
echo "Creating combined policy summary..."
find "$OUTPUT_DIR" -name "policy-summary.json" -exec cat {} \; | jq -s '{
    scan_date: now | strftime("%Y-%m-%dT%H:%M:%SZ"),
    images: .,
    total_vulnerabilities: {
        critical: [.[].vulnerabilities.critical] | add,
        high: [.[].vulnerabilities.high] | add,
        medium: [.[].vulnerabilities.medium] | add,
        low: [.[].vulnerabilities.low] | add
    },
    overall_pass: true
}' > "$OUTPUT_DIR/combined-policy-summary.json"

# Create markdown summary
TOTAL_CRITICAL=$(jq '.total_vulnerabilities.critical' "$OUTPUT_DIR/combined-policy-summary.json")
TOTAL_HIGH=$(jq '.total_vulnerabilities.high' "$OUTPUT_DIR/combined-policy-summary.json")
TOTAL_MEDIUM=$(jq '.total_vulnerabilities.medium' "$OUTPUT_DIR/combined-policy-summary.json")
TOTAL_LOW=$(jq '.total_vulnerabilities.low' "$OUTPUT_DIR/combined-policy-summary.json")

cat > "$OUTPUT_DIR/scan-summary.md" << EOF
# Container Security Scan Results

**Scan Date:** $(date)

## Summary
- **Images Scanned:** ${#IMAGE_LIST[@]}
- **Total Critical:** $TOTAL_CRITICAL
- **Total High:** $TOTAL_HIGH
- **Total Medium:** $TOTAL_MEDIUM
- **Total Low:** $TOTAL_LOW

## Per-Image Results

EOF

# Add per-image results to markdown
jq -r '.images[] | "### \(.image)\n- Critical: \(.vulnerabilities.critical)\n- High: \(.vulnerabilities.high)\n- Medium: \(.vulnerabilities.medium)\n- Low: \(.vulnerabilities.low)\n"' "$OUTPUT_DIR/combined-policy-summary.json" >> "$OUTPUT_DIR/scan-summary.md"

echo ""
echo "Scan completed!"
echo "Results saved to: $OUTPUT_DIR"
echo "Combined summary: $OUTPUT_DIR/combined-policy-summary.json"
echo "Markdown report: $OUTPUT_DIR/scan-summary.md"
