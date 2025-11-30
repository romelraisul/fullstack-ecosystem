# This file contains the main Terraform configuration for your GCP infrastructure.
# It defines the provider, network, firewall rules, and the gateway VM.

provider "google" {
  project     = var.gcp_project_id
  region      = var.gcp_region
}

# Reserve a static IP address in the new region
resource "google_compute_address" "static_ip_asia" {
  name   = "vm-static-ip-asia"
  region = var.gcp_region
}

# Define the Compute Engine instance
resource "google_compute_instance" "app_server" {
  name         = "migrated-vm-asia"
  machine_type = "e2-micro"
  can_ip_forward = true
  zone         = var.gcp_zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.static_ip_asia.address
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  metadata = {
    ssh-keys = "romelraisul:${file("~/.ssh/id_rsa.pub")}"
  }

  metadata_startup_script = templatefile("${path.module}/startup_script.sh", {
    server_private_key = var.server_private_key,
    client_public_key  = var.client_public_key,
    server_wg_ip       = "10.10.0.1/24",
    client_wg_ip       = "10.10.0.2/32",
    ETH_INTERFACE      = "eth0"
  })

  service_account {
    scopes = ["cloud-platform"]
  }
}

# Output the new public IP address
output "new_public_ip" {
  value       = google_compute_instance.app_server.network_interface[0].access_config[0].nat_ip
  description = "The new public IP address of the Asia-based VM."
}

# Add your resource definitions here based on the blueprint.
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}
