#!/bin/bash
# SSH Diagnostics Script for GCP VM
# Run this via Serial Console or Browser SSH when direct SSH fails

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SSH DIAGNOSTICS & REPAIR TOOL${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"

# Check 1: SSH Daemon Status
echo -e "${CYAN}[1] Checking SSH daemon status...${NC}"
if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
    echo -e "${GREEN}✓ SSH daemon is running${NC}"
    systemctl status sshd 2>/dev/null || systemctl status ssh 2>/dev/null | head -3
else
    echo -e "${RED}✗ SSH daemon is NOT running${NC}"
    echo "  Attempting to start..."
    sudo systemctl start sshd 2>/dev/null || sudo systemctl start ssh 2>/dev/null || sudo service ssh start
    if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
        echo -e "${GREEN}✓ SSH daemon started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start SSH daemon. Check logs: sudo journalctl -u sshd -n 50${NC}"
    fi
fi

# Check 2: SSH Port Listening
echo -e "\n${CYAN}[2] Checking SSH port (22)...${NC}"
if ss -tlnp 2>/dev/null | grep -q ':22 ' || netstat -tlnp 2>/dev/null | grep -q ':22 '; then
    echo -e "${GREEN}✓ SSH is listening on port 22${NC}"
    ss -tlnp 2>/dev/null | grep ':22 ' || netstat -tlnp 2>/dev/null | grep ':22 '
else
    echo -e "${RED}✗ SSH is NOT listening on port 22${NC}"
    echo "  Check /etc/ssh/sshd_config for 'Port' directive"
fi

# Check 3: Network Interfaces
echo -e "\n${CYAN}[3] Checking network interfaces...${NC}"
ip -br a 2>/dev/null || ifconfig
EXTERNAL_IP=$(curl -s -m 5 ifconfig.me 2>/dev/null || echo "unavailable")
echo -e "External IP: ${YELLOW}$EXTERNAL_IP${NC}"

# Check 4: Internal Firewall (ufw/firewalld)
echo -e "\n${CYAN}[4] Checking internal firewall...${NC}"
if command -v ufw &>/dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
    echo "ufw: $UFW_STATUS"
    if [[ "$UFW_STATUS" == *"active"* ]]; then
        sudo ufw status | grep 22 || echo -e "${YELLOW}⚠ Port 22 not explicitly allowed in ufw${NC}"
    fi
elif command -v firewall-cmd &>/dev/null; then
    echo "firewalld: $(sudo firewall-cmd --state 2>/dev/null || echo 'not running')"
    sudo firewall-cmd --list-services 2>/dev/null | grep -q ssh && echo -e "${GREEN}✓ SSH service allowed${NC}" || echo -e "${YELLOW}⚠ SSH not in allowed services${NC}"
else
    echo -e "${GREEN}✓ No ufw or firewalld detected${NC}"
fi

# Check 5: SSH Config
echo -e "\n${CYAN}[5] SSH daemon configuration (/etc/ssh/sshd_config):${NC}"
echo "Port: $(grep -E "^Port " /etc/ssh/sshd_config 2>/dev/null || echo '22 (default)')"
echo "PermitRootLogin: $(grep -E "^PermitRootLogin " /etc/ssh/sshd_config 2>/dev/null || echo 'default')"
echo "PubkeyAuthentication: $(grep -E "^PubkeyAuthentication " /etc/ssh/sshd_config 2>/dev/null || echo 'yes (default)')"
echo "PasswordAuthentication: $(grep -E "^PasswordAuthentication " /etc/ssh/sshd_config 2>/dev/null || echo 'default')"

# Check 6: Authorized Keys for Current User
echo -e "\n${CYAN}[6] Checking SSH keys for $USER...${NC}"
if [ -d "$HOME/.ssh" ]; then
    echo "Directory: $HOME/.ssh"
    ls -la "$HOME/.ssh/" 2>/dev/null | head -10
    if [ -f "$HOME/.ssh/authorized_keys" ]; then
        KEY_COUNT=$(wc -l < "$HOME/.ssh/authorized_keys")
        echo -e "${GREEN}✓ authorized_keys exists: $KEY_COUNT keys${NC}"
        echo "Permissions: $(ls -l $HOME/.ssh/authorized_keys | awk '{print $1}')"
    else
        echo -e "${YELLOW}⚠ No authorized_keys file found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No .ssh directory found${NC}"
fi

# Check 7: Recent SSH Auth Logs
echo -e "\n${CYAN}[7] Recent SSH authentication attempts:${NC}"
if [ -f /var/log/auth.log ]; then
    echo "Last 10 SSH-related entries from /var/log/auth.log:"
    sudo tail -20 /var/log/auth.log | grep -i ssh | tail -10 || echo "No recent SSH entries"
elif command -v journalctl &>/dev/null; then
    echo "Last 10 SSH-related entries from journalctl:"
    sudo journalctl -u sshd -u ssh -n 10 --no-pager 2>/dev/null || echo "No journal entries"
else
    echo -e "${YELLOW}⚠ No accessible logs found${NC}"
fi

# Check 8: OS Login Status
echo -e "\n${CYAN}[8] Checking OS Login configuration...${NC}"
if command -v google_oslogin_nss_cache &>/dev/null; then
    echo -e "${GREEN}✓ OS Login NSS module installed${NC}"
    if grep -q "google_authorized_keys" /etc/ssh/sshd_config 2>/dev/null; then
        echo -e "${GREEN}✓ OS Login configured in sshd_config${NC}"
    else
        echo -e "${YELLOW}⚠ OS Login binary present but not configured in sshd_config${NC}"
    fi
else
    echo -e "${YELLOW}⚠ OS Login not installed (using metadata keys)${NC}"
fi

# Repair Options
echo -e "\n${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  QUICK FIXES${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"

echo "Run these commands if needed:"
echo ""
echo -e "${YELLOW}# Restart SSH daemon:${NC}"
echo "  sudo systemctl restart sshd || sudo systemctl restart ssh"
echo ""
echo -e "${YELLOW}# Fix .ssh permissions (if you have keys):${NC}"
echo "  chmod 700 ~/.ssh"
echo "  chmod 600 ~/.ssh/authorized_keys"
echo "  chown -R \$USER:\$USER ~/.ssh"
echo ""
echo -e "${YELLOW}# Allow SSH in ufw (if blocking):${NC}"
echo "  sudo ufw allow 22/tcp"
echo "  sudo ufw reload"
echo ""
echo -e "${YELLOW}# Check detailed SSH logs:${NC}"
echo "  sudo journalctl -u sshd -f"
echo "  sudo tail -f /var/log/auth.log"
echo ""
echo -e "${YELLOW}# Test SSH locally:${NC}"
echo "  ssh -v localhost"
echo ""
echo -e "${GREEN}Diagnostics complete!${NC}\n"
