# This file contains Terraform definitions for Windows RDP virtual machines on Proxmox.

resource "proxmox_virtual_environment_vm" "windows_workstation" {
  count     = 1
  name      = "win11-workstation-${count.index + 1}"
  node_name = "pve"
  
  # New machine ID will start from 101
  vm_id     = 101 + count.index

  clone {
    # Using your actual template ID
    vm_id     = 100
    full      = true
    retries   = 3
    datastore_id = "local-lvm"
  }

  cpu {
    cores = 4
    type  = "host"
  }

  memory {
    dedicated = 8192
  }

  network_device {
    bridge = "vmbr0"
    model  = "virtio"
  }

  agent {
    enabled = true
  }

  operating_system {
    type = "win11"
  }
}
