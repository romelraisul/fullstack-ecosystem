import logging
import json
import time
import sys
import yaml
import os
from datetime import datetime
from proxmoxer import ProxmoxAPI
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger("LXCDeploy")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("ansible_deploy.log")
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler(sys.stdout))

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

def get_next_vmid(prox):
    cluster_resources = prox.cluster.resources.get(type="vm")
    ids = [int(vm['vmid']) for vm in cluster_resources]
    return max(ids) + 1 if ids else 100

def ensure_template(prox, node, storage, target_template):
    try:
        content = prox.nodes(node).storage(storage).content.get(content='vztmpl')
        target_os = "ubuntu-22.04"
        for item in content:
            if target_os in item['volid']:
                return item['volid']
        for item in content:
            if "ubuntu" in item['volid']:
                return item['volid']
    except Exception as e:
        logger.error(f"Template check failed: {e}")
    return None

def deploy_lxc(config):
    prox = connect_proxmox(config['proxmox'])
    node = config['proxmox']['node']
    specs = config['container_specs']
    
    vmid = get_next_vmid(prox)
    hostname = f"{specs['prefix']}-01"
    
    storage_name = specs['ostemplate'].split(':')[0]
    final_template = ensure_template(prox, node, storage_name, specs['ostemplate'])
    
    if not final_template:
        logger.error("No valid template found. Please download Ubuntu 22.04 template manually.")
        return 1

    logger.info(f"Deploying {hostname} (ID: {vmid}) IP: {specs.get('ipv4_address', 'dhcp')}")

    net_config = f"name=eth0,bridge={specs['network_bridge']}"
    if 'ipv4_address' in specs:
        net_config += f",ip={specs['ipv4_address']},gw={specs['gateway']}"
    else:
        net_config += ",ip=dhcp"

    # Read Public Key if exists
    ssh_key = None
    key_path = r"G:\My Drive\Automations\hybrid-cloud-setup\keys\ansible_key.pub"
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            ssh_key = f.read().strip()
    
    params = {
        "vmid": vmid,
        "hostname": hostname,
        "ostemplate": final_template,
        "password": specs['password'],
        "cores": specs['cores'],
        "memory": specs['memory'],
        "swap": specs['swap'],
        "rootfs": f"{specs['storage_id']}:{specs['disk_size']}",
        "net0": net_config,
        "start": 1
    }
    if ssh_key:
        params["ssh-public-keys"] = ssh_key

    try:
        prox.nodes(node).lxc.post(**params)
        logger.info(f"Deployment Request Sent! VMID: {vmid}")
        return 0
    except Exception as e:
        logger.error(f"Deployment Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(deploy_lxc(load_config()))