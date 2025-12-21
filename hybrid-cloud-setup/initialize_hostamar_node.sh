#!/bin/bash
set -e

# --- HOSTAMAR AUTOMATED DEPLOYMENT ---
# Target: Ubuntu 24.04 (LXC Container 105)
# Function: Hybrid Cloud Node Initialization

echo "[INFO] Starting Hostamar Initialization..."

# 1. System Updates & Dependencies
echo "[INFO] Updating system packages..."
apt-get update && apt-get upgrade -y
apt-get install -y wireguard resolvconf curl git docker.io docker-compose openssh-server

# 2. Configure WireGuard Tunnel (Client)
echo "[INFO] Configuring WireGuard..."
umask 077
# Generate keys if they don't exist
if [ ! -f private.key ] || [ ! -s private.key ]; then
    echo "[INFO] Generating new WireGuard keys..."
    wg genkey | tee private.key | wg pubkey > public.key
fi

CLIENT_PRIV=$(cat private.key)
CLIENT_PUB=$(cat public.key)

if [ -z "$CLIENT_PRIV" ]; then
    echo "[ERROR] Private key generation failed. Aborting."
    exit 1
fi

# GCP Server Details (From previous steps)
GCP_PUB_KEY="yPos1el6LluAVLgfbo71D2dn21eyxQkLeULYP+hj73w="
GCP_ENDPOINT="34.131.107.91:51820"

cat <<EOF > /etc/wireguard/wg0.conf
[Interface]
Address = 10.10.10.2/24
PrivateKey = $CLIENT_PRIV
DNS = 8.8.8.8
MTU = 1280
PostUp = iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

[Peer]
PublicKey = $GCP_PUB_KEY
Endpoint = $GCP_ENDPOINT
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

# Enable & Start Tunnel
systemctl enable wg-quick@wg0
systemctl restart wg-quick@wg0

# 3. Configure SSH & Auditing
echo "[INFO] Securing SSH..."
# Enable logging
echo "LogLevel VERBOSE" >> /etc/ssh/sshd_config
# Ensure PubKey Auth is on
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config # Keep password for now until key is verified
systemctl restart ssh

# 4. Deploy Business Services (Docker)
echo "[INFO] Deploying Business Units..."
mkdir -p /opt/hostamar/services
cd /opt/hostamar/services

# Create Docker Compose Files
cat <<EOF > docker-compose-dbaas.yml
version: '3.8'
services:
  postgres_primary:
    image: postgres:15
    container_name: dbaas_postgres
    restart: always
    environment:
      POSTGRES_PASSWORD: "SuperSecurePassword123!"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  portainer:
    image: portainer/portainer-ce:latest
    container_name: dbaas_manager
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    ports:
      - "9000:9000"
volumes:
  postgres_data:
  portainer_data:
EOF

# Start Services
docker-compose -f docker-compose-dbaas.yml up -d

echo "---------------------------------------------------"
echo "       HOSTAMAR DEPLOYMENT COMPLETE"
echo "---------------------------------------------------"
echo "1. WireGuard Public Key: $CLIENT_PUB"
echo "   (ACTION REQUIRED: Add this key to GCP WireGuard Config)"
echo "2. SSH is active on Port 22."
echo "3. Portainer (DB Manager) is active on Port 9000."
echo "4. VPN Status: $(systemctl is-active wg-quick@wg0)"
echo "---------------------------------------------------"
