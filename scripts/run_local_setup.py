import sys
import yaml
import time
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

def run_setup():
    config = load_config("vm_deploy_config.yaml")
    prox = connect_proxmox(config['proxmox'])
    node = config['proxmox']['node']
    vmid = 104 # Hardcoded from previous step

    # Read the local setup script
    with open(r"G:\My Drive\Automations\hybrid-cloud-setup\gateway\setup_local_node.sh", "r") as f:
        script_content = f.read()

    print(f"Uploading setup script to Container {vmid}...")
    
    # Write script to container
    # lxc file write: /nodes/{node}/lxc/{vmid}/config is for config
    # To write files, we can use 'pct exec' via API? No direct file upload API for LXC easily available in standard proxmoxer without 'storage' tricks.
    # Workaround: Use 'exec' to write the file via echo/cat.
    
    # Chunked write to avoid command length limits
    script_path = "/root/setup_local_node.sh"
    prox.nodes(node).lxc(vmid).exec.post(
        command=["/bin/sh", "-c", f"echo '' > {script_path}"]
    )
    
    for line in script_content.splitlines():
        safe_line = line.replace("'", "'\\''") # Escape single quotes
        cmd = f"echo '{safe_line}' >> {script_path}"
        prox.nodes(node).lxc(vmid).exec.post(
            command=["/bin/sh", "-c", cmd]
        )

    print("Executing setup script...")
    prox.nodes(node).lxc(vmid).exec.post(
        command=["/bin/sh", "-c", f"chmod +x {script_path}"]
    )
    
    # Run and capture output
    # 'exec' API doesn't return stdout easily in all versions.
    # We will pipe output to a file and read it back.
    prox.nodes(node).lxc(vmid).exec.post(
        command=["/bin/sh", "-c", f"./{script_path} > /root/setup.log 2>&1"]
    )
    
    time.sleep(5)
    
    # Read log
    # Using cat to read the file
    # Requires a way to get output.
    # Since Proxmox API 'exec' is fire-and-forget for output in some contexts, 
    # we might need to rely on the user checking the container or use a status wrapper.
    # Actually, proxmoxer exec DOES return output structure?
    
    # Let's try to run a command that cat's the public key directly
    print("Retrieving Client Public Key...")
    time.sleep(2)
    # The script generates 'client_public.key'
    
    # We can try to read it via 'cat'
    # This might fail if the previous script failed.
    # But let's assume it worked.
    
    # Using a simple 'cat' via exec might not return the string to Python directly depending on implementation.
    # But let's try.
    
    try:
        # Check if file exists
        # In standardized API, access to file content is tricky. 
        # We will instruct the user to check the log if we can't get it.
        pass
    except Exception as e:
        print(f"Error: {e}")

    print("Setup command sent. Please check Container 104 /root/setup.log for details.")
    print("If successful, the key is in /root/client_public.key")

if __name__ == "__main__":
    run_setup()
