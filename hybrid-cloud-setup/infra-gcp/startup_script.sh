#!/bin/bash
set -e
set -x

# Install WireGuard
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y wireguard iptables-persistent

# Create WireGuard configuration
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.10.0.1/24
SaveConfig = true
PrivateKey = ${server_private_key}
ListenPort = 51820

[Peer]
PublicKey = zNrf3v6qlYYzD4BCXhE3iEYwA/Tz/O92mamNikKQqBQ=
AllowedIPs = 10.10.0.2/32
EOF

# Enable IP Forwarding
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

# Configure NAT
ETH_INTERFACE=$(ip -o -4 route show to default | awk '{print $5}')
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o $ETH_INTERFACE -j MASQUERADE
netfilter-persistent save

# Enable and start WireGuard service
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
