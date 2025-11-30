# This file defines the input variables for the GCP infrastructure module.

variable "gcp_project_id" {
  description = "The ID of your Google Cloud project."
  type        = string
}



variable "gcp_region" {
  description = "The GCP region to deploy resources into."
  type        = string
  default     = "asia-south1"
}

variable "gcp_zone" {
  description = "The GCP zone to deploy resources into."
  type        = string
  default     = "asia-south1-b"
}

variable "server_private_key" {
  description = "The WireGuard private key for the server."
  type        = string
}

variable "server_public_key" {
  description = "The WireGuard public key for the server."
  type        = string
}

variable "client_public_key" {
  description = "The WireGuard public key for the client."
  type        = string
}

variable "startup_script_path" {
  description = "The path to the startup script file."
  type        = string
  default     = "startup_script.sh"
}

variable "ssh_public_key" {
  description = "The public SSH key for the VM user."
  type        = string
}

variable "vm1_public_key" {
  description = "The WireGuard public key for the first new VM."
  type        = string
}




