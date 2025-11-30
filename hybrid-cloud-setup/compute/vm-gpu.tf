# This file contains Terraform definitions for VMs with GPU passthrough for video editing.

# resource "proxmox_vm_qemu" "gpu_workstation" {
#   name        = "video-editing-vm"
#   target_node = "pve"
#   # ... other VM settings
#
#   # GPU Passthrough
#   hostpci0 = {
#     host = "0000:01:00.0" # Example PCI address
#     pcie = "1"
#   }
# }
