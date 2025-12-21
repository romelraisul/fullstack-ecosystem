import sys
import yaml
import time
import os
from proxmoxer import ProxmoxAPI
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def load_config(path="vm_deploy_config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def connect_proxmox(config):
    return ProxmoxAPI(
        config['host'],
        user=config['user'],
        token_name=config['token_id'],
        token_value=config['token_secret'],
        verify_ssl=config['verify_ssl']
    )

def provision_stack():
    config = load_config("vm_deploy_config.yaml")
    prox = connect_proxmox(config['proxmox'])
    node = config['proxmox']['node']
    vmid = 105 # New ID for the Automation Stack

    # 1. Check if container exists, else create (using logic from vm_deploy.py)
    # For brevity, I'll assume we are reusing or creating a new one with ID 105.
    
    # 2. Preparation of the setup script
    setup_script = """#!/bin/bash
# Install Docker
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Setup project directory
mkdir -p /opt/automation
cd /etc/automation
"""

    # 3. Upload Docker Compose and Prometheus config
    # We will use 'exec' to write them as we did in run_local_setup.py
    files_to_upload = {
        "/opt/automation/docker-compose.yaml": r"G:\My Drive\Automations\infrastructure\docker-compose.yaml",
        "/opt/automation/prometheus.yml": r"G:\My Drive\Automations\infrastructure\prometheus.yml"
    }

    print(f"Provisioning Automation Stack on Container {vmid}...")

    for remote_path, local_path in files_to_upload.items():
        with open(local_path, "r") as f:
            content = f.read()
        
        # Create directory
        dir_path = os.path.dirname(remote_path)
        prox.nodes(node).lxc(vmid).exec.post(command=["mkdir", "-p", dir_path])
        
        # Write file (chunked or simple echo for smaller files)
        prox.nodes(node).lxc(vmid).exec.post(command=["/bin/sh", "-c", f"cat <<EOF > {remote_path}\n{content}\nEOF"])
        print(f"Uploaded {remote_path}")

    # 4. Start the stack
    print("Starting Docker Compose stack...")
    prox.nodes(node).lxc(vmid).exec.post(
        command=["/bin/sh", "-c", "cd /opt/automation && docker compose up -d"]
    )

    print("Stack deployment initiated. Access Grafana on port 3000 and Ollama on port 11434.")

if __name__ == "__main__":
    provision_stack()
