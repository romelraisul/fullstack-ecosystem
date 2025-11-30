#!/bin/bash

# SSH Connection Script for Mumbai VM
# Auto-generated based on your configuration

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== GCP Mumbai VM SSH Setup ===${NC}\n"

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✓ Project: $PROJECT_ID${NC}"

# Check if VM exists
VM_NAME="mumbai-instance-1"
ZONE="asia-south1-a"

echo -e "${YELLOW}Checking VM status...${NC}"
VM_STATUS=$(gcloud compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(status)' 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
    echo -e "${RED}Error: VM '$VM_NAME' not found in zone '$ZONE'${NC}"
    echo "Available instances:"
    gcloud compute instances list
    exit 1
fi

echo -e "${GREEN}✓ VM Status: $VM_STATUS${NC}"

if [ "$VM_STATUS" != "RUNNING" ]; then
    echo -e "${YELLOW}VM is not running. Starting...${NC}"
    gcloud compute instances start "$VM_NAME" --zone="$ZONE"
    echo "Waiting 30 seconds for VM to boot..."
    sleep 30
fi

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo -e "${GREEN}✓ External IP: $EXTERNAL_IP${NC}"

# Configure SSH
echo -e "\n${YELLOW}Configuring SSH...${NC}"
gcloud compute config-ssh --quiet 2>/dev/null || true

# Build host alias
HOST_ALIAS="$VM_NAME.$ZONE.$PROJECT_ID"

echo -e "${GREEN}✓ SSH Host Alias: $HOST_ALIAS${NC}"

# Test connection
echo -e "\n${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$HOST_ALIAS" "echo 'Connection successful!'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful!${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo -e "\n${YELLOW}Trying alternative method with gcloud ssh...${NC}"
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="echo 'Connection successful!'" 2>/dev/null; then
        echo -e "${GREEN}✓ gcloud ssh works!${NC}"
        HOST_ALIAS="gcloud:$VM_NAME:$ZONE"
    else
        echo -e "${RED}Error: Cannot connect to VM${NC}"
        echo "Check: 1) VM is running, 2) Firewall allows port 22, 3) SSH keys are configured"
        exit 1
    fi
fi

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   SSH Configuration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Connect using:${NC}"
echo -e "  ssh $HOST_ALIAS"
echo ""
echo -e "${YELLOW}Or use gcloud directly:${NC}"
echo -e "  gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo -e "${YELLOW}For VS Code Remote SSH:${NC}"
echo -e "  1. Press F1 → 'Remote-SSH: Connect to Host'"
echo -e "  2. Select: $HOST_ALIAS"
echo ""
echo -e "${YELLOW}Project directory on VM:${NC}"
echo -e "  ssh $HOST_ALIAS 'mkdir -p ~/hostamar-platform'"
echo ""
echo -e "${GREEN}Ready for deployment! Run: bash deploy/gcp-mumbai-deploy.sh${NC}"
