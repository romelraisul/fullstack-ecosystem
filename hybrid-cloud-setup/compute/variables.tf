variable "proxmox_api_url" {
  type        = string
  description = "Proxmox API URL (e.g., https://192.168.1.5:8006/)"
}

variable "proxmox_password" {
  type        = string
  sensitive   = true
  description = "Proxmox root password"
}

variable "business_modules" {
  description = "List of business models to deploy."
  type        = list(string)
  default     = []
}
