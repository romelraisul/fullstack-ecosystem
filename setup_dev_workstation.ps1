<#
.SYNOPSIS
    Automates the setup of a modern Windows development workstation using Chocolatey for package management,
    installs essential development tools, and configures a WireGuard VPN client.

.DESCRIPTION
    This PowerShell script performs the following actions:
    1.  Ensures it is run with Administrator privileges.
    2.  Installs the Chocolatey package manager if it's not already present.
    3.  Uses Chocolatey to install a suite of development tools:
        - Git (git.install)
        - Python 3 (python3)
        - Visual Studio Code (vscode)
        - Google Chrome (googlechrome)
        - WireGuard (wireguard)
    4.  Refreshes environment variables to make newly installed tools available in the current session.
    5.  Performs basic Git configuration (placeholders for user name and email).
    6.  Automates the generation of a WireGuard key pair.
    7.  Creates a template WireGuard configuration file (`wg0.conf`) in the user's home directory.
    8.  Provides verification steps and instructions for completing the WireGuard configuration.

.NOTES
    Author: GitHub Copilot
    Date: 26-11-2025
    Requires: Windows PowerShell 5.1 or later, running as Administrator.
#>

# Step 1: Verify Administrator Privileges
if (-Not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script must be run as an Administrator. Please restart the shell with 'Run as Administrator'."
    Start-Sleep -Seconds 10
    exit 1
}

# --- Phase 1: Bootstrapping (Chocolatey Installation) ---
Write-Host "Phase 1: Bootstrapping Chocolatey..." -ForegroundColor Green

# Check if Chocolatey is installed
$chocoPath = Join-Path $env:ProgramData "chocolatey\bin\choco.exe"
if (Test-Path $chocoPath) {
    Write-Host "Chocolatey is already installed."
} else {
    Write-Host "Installing Chocolatey..."
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force;
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "Chocolatey installed successfully." -ForegroundColor Green
    } catch {
        Write-Error "Failed to install Chocolatey. Please check your internet connection and permissions."
        exit 1
    }
}

# Ensure Chocolatey commands are available in the current session
Import-Module -Name chocolatey -Force

# --- Phase 2: Package Hydration (Payload Installation) ---
Write-Host "`nPhase 2: Installing core development tools..." -ForegroundColor Green

$packages = @(
    @{ Name = "Git"; ID = "git.install" },
    @{ Name = "Python 3"; ID = "python3" },
    @{ Name = "Visual Studio Code"; ID = "vscode" },
    @{ Name = "Google Chrome"; ID = "googlechrome" },
    @{ Name = "WireGuard"; ID = "wireguard" }
)

foreach ($pkg in $packages) {
    Write-Host "Installing $($pkg.Name) ($($pkg.ID))..."
    # Check if the package is already installed to avoid reinstallation
    if (choco list --local-only --exact --id-only -r $($pkg.ID)) {
        Write-Host "$($pkg.Name) is already installed. Skipping."
    } else {
        choco install $($pkg.ID) --confirm --no-progress
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-Host "$($pkg.Name) installed successfully."
        } elseif ($exitCode -eq 3010) {
            Write-Warning "$($pkg.Name) installation requires a reboot. Please reboot your system after the script finishes."
        } else {
            Write-Error "Failed to install $($pkg.Name). Exit code: $exitCode. Check the logs at C:\ProgramData\chocolatey\logs\chocolatey.log"
        }
    }
}

# --- Phase 3: Configuration and Hardening ---
Write-Host "`nPhase 3: Configuring tools and network..." -ForegroundColor Green

# Refresh environment variables to recognize new PATH entries
Write-Host "Refreshing environment variables..."
refreshenv

# Basic Git Configuration
Write-Host "Configuring Git..."
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global core.autocrlf true
Write-Host "Git configured with placeholder user. Please update with 'git config --global user.name' and 'user.email'."

# WireGuard Configuration
Write-Host "Configuring WireGuard..."
$wireguardDir = "C:\Program Files\WireGuard"
$wgExe = Join-Path $wireguardDir "wg.exe"

if (-Not (Test-Path $wgExe)) {
    Write-Error "WireGuard executable (wg.exe) not found at '$wireguardDir'. Cannot proceed with WireGuard configuration."
} else {
    # Generate Keys
    Write-Host "Generating WireGuard key pair..."
    $privateKey = & $wgExe genkey
    $publicKey = $privateKey | & $wgExe pubkey

    # Create Configuration File Template
    $wgConfigFile = Join-Path $env:USERPROFILE "wg0.conf"
    $wgConfigContent = @"
# This is a template configuration file for WireGuard client.
# Generated by PowerShell automation script.
#
# Your Public Key (share this with the server administrator): $publicKey
#
# PLEASE EDIT THE FOLLOWING SECTIONS:

[Interface]
# Client's Private Key (DO NOT SHARE)
PrivateKey = $privateKey
# Client's IP address within the VPN subnet
Address = 10.0.0.2/32
# DNS server to use when the tunnel is active (prevents DNS leaks)
DNS = 1.1.1.1

[Peer]
# Server's Public Key (get this from the server administrator)
PublicKey = SERVER_PUBLIC_KEY_HERE
# The server's public IP address and port
Endpoint = SERVER_PUBLIC_IP:51820
# Routes all traffic through the VPN. For split-tunnel, specify the VPN subnet (e.g., 10.0.0.0/24)
AllowedIPs = 0.0.0.0/0
# Keeps the connection alive through NAT firewalls
PersistentKeepalive = 25
"@

    Set-Content -Path $wgConfigFile -Value $wgConfigContent
    Write-Host "WireGuard configuration template created at '$wgConfigFile'." -ForegroundColor Yellow
    Write-Host "IMPORTANT: You must edit this file to add the server's public key and endpoint."
}

# --- Phase 4: Verification ---
Write-Host "`nPhase 4: Verifying installations..." -ForegroundColor Green

try {
    Write-Host "Git Version:"
    git --version
    Write-Host "Python Version:"
    python --version
    Write-Host "VS Code Version:"
    code --version
} catch {
    Write-Warning "Verification failed for one or more tools. A system reboot might be required to update the PATH variable correctly."
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Automated Workstation Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next Steps:"
Write-Host "1. Update your Git configuration with your actual name and email."
Write-Host "   - git config --global user.name ""Your Name"""
Write-Host "   - git config --global user.email ""you@example.com"""
Write-Host "2. Edit the WireGuard configuration file: $wgConfigFile"
Write-Host "   - Replace 'SERVER_PUBLIC_KEY_HERE' and 'SERVER_PUBLIC_IP'."
Write-Host "   - Adjust 'Address' and 'AllowedIPs' as needed."
Write-Host "3. Import the .conf file into the WireGuard application and activate the tunnel."
Write-Host "4. A reboot may be necessary for all changes to take full effect."
