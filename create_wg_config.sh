#!/bin/bash
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.10.0.1/24
SaveConfig = true
PrivateKey = ${srvprv}
ListenPort = 51820

[Peer]
PublicKey = ${clpub}
AllowedIPs = 10.10.0.2/32
EOF
