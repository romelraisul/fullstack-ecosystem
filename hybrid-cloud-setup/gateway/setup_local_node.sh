#!/bin/bash

# Local Node Setup Script (Ryzen 9900X / Proxmox)
# Connects to GCP Gateway (hostamar-prod)

# 1. Install WireGuard
sudo apt update
sudo apt install -y wireguard resolvconf

# 2. Generate Client Keys
umask 077
wg genkey | tee client_private.key | wg pubkey > client_public.key
CLIENT_PRIV_KEY=$(cat client_private.key)
CLIENT_PUB_KEY=$(cat client_public.key)

echo "Client Public Key: $CLIENT_PUB_KEY"
echo ">> COPY THIS KEY and add it to the [Peer] section on your GCP Server <<"

# 3. Configure WireGuard Interface (wg0)
# GCP Endpoint: 34.131.107.91 (hostamar-prod)
cat <<EOF | sudo tee /etc/wireguard/wg0.conf
[Interface]
Address = 10.10.10.2/24
PrivateKey = $CLIENT_PRIV_KEY
DNS = 8.8.8.8
MTU = 1280
PostUp = iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

[Peer]
PublicKey = yPos1el6LluAVLgfbo71D2dn21eyxQkLeULYP+hj73w=
Endpoint = 34.131.107.91:51820
AllowedIPs = 10.10.10.0/24
PersistentKeepalive = 25
EOF

echo "Configuration created at /etc/wireguard/wg0.conf"
echo "Step 1: Replace GCP_SERVER_PUBLIC_KEY_PLACEHOLDER in /etc/wireguard/wg0.conf"
echo "Step 2: Start the tunnel: sudo wg-quick up wg0"