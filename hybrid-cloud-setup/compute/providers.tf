terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.66.1"
    }
  }
}

provider "proxmox" {
  endpoint = var.proxmox_api_url
  username = "root@pam"
  password = var.proxmox_password
  insecure = true
  tmp_dir  = "/var/tmp"
  ssh {
    agent = false
  }
}
