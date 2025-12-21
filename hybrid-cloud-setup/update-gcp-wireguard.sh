#!/bin/bash
# Update GCP WireGuard Server with new Windows client

set -e

echo "==========================================="
echo "Updating GCP WireGuard Server Configuration"
echo "==========================================="

# New Windows client public key
WINDOWS_CLIENT_PUBKEY="uxyYJY25iWos+IfkSH9Wc9v7lRGEEqrm2F4py5RdxAw="

echo "Connecting to GCP server (34.131.107.91)..."

# SSH to GCP and update WireGuard config
ssh -i ~/.ssh/id_rsa root@34.131.107.91 << 'ENDSSH'
# Add Windows client peer to WireGuard
wg set wg0 peer XTAAjnYgjnpLjpV9ZJ3a2Ke0n8o0jP4KYwfH1bXShHA= allowed-ips 10.10.0.2/32

# Save configuration
wg-quick save wg0

# Show current status
echo ""
echo "Current WireGuard Status:"
wg show

echo ""
echo "Configuration updated successfully!"
ENDSSH

echo ""
echo "==========================================="
echo "GCP Server Updated Successfully!"
echo "==========================================="
echo ""
echo "Now activate the tunnel on Windows:"
echo "1. Open WireGuard app"
echo "2. Find 'gcp_tunnel' in the list"
echo "3. Click 'Activate'"
echo ""
echo "Test connectivity:"
echo "  ping 10.10.0.1  (GCP server)"
echo "==========================================="
