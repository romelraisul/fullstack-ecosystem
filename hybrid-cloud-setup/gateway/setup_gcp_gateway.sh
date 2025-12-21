#!/bin/bash

# Hybrid Cloud Gateway Setup Script (GCP hostamar-prod)
# Zone: asia-south2-b
# Internal IP: 10.190.0.2
# External IP: 34.131.107.91

# 1. System Update & Install Dependencies
echo "Updating system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y wireguard nginx qrencode iptables-persistent

# 2. Enable IP Forwarding
echo "Enabling IP Forwarding..."
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 3. Generate WireGuard Keys
echo "Generating Keys..."
umask 077
wg genkey | tee server_private.key | wg pubkey > server_public.key
SERVER_PRIV_KEY=$(cat server_private.key)
SERVER_PUB_KEY=$(cat server_public.key)

echo "GCP Server Public Key: $SERVER_PUB_KEY"

# 4. Configure WireGuard Interface (wg0)
# GCP Internal IP is 10.190.0.2, but WireGuard Tunnel IP will be 10.10.10.1
cat <<EOF | sudo tee /etc/wireguard/wg0.conf
[Interface]
Address = 10.10.10.1/24
SaveConfig = true
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
ListenPort = 51820
PrivateKey = $SERVER_PRIV_KEY

# Local Node (Ryzen Server at 192.168.1.83) Peer
[Peer]
# Replace with the CLIENT_PUBLIC_KEY generated on your local machine
PublicKey = CLIENT_PUBLIC_KEY_PLACEHOLDER
AllowedIPs = 10.10.10.2/32
EOF

# 5. Enable & Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# 6. Configure Nginx Reverse Proxy
# Proxies traffic from GCP Public IP (34.131.107.91) -> Tunnel -> Local Node (10.10.10.2)
cat <<EOF | sudo tee /etc/nginx/sites-available/hostamar_proxy
server {
    listen 80;
    server_name _;  # Accepts traffic on 34.131.107.91

    location / {
        proxy_pass http://10.10.10.2:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings for long-running connections (e.g., RDP/WebSockets)
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/hostamar_proxy /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "Setup Complete!"
echo "Action Required:"
echo "1. Copy the GCP Server Public Key above."
echo "2. Run 'setup_local_node.sh' on your Local Ryzen Server."
echo "3. Paste your Local Node's Public Key into /etc/wireguard/wg0.conf on this server."