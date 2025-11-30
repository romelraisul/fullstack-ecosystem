provider "google" {
  credentials = "C:/Users/romel/OneDrive/Documents/aiauto/arafat-468807-daf06a5538d8.json"
  project     = "arafat-468807"
  region      = "us-central1"
}

resource "google_compute_instance" "vpn_gateway" {
  name         = "hybrid-cloud-gateway"
  machine_type = "e2-micro" # Free Tier
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network = "default"
    access_config {} # This will assign a public IP
  }

  

  tags = ["vpn-server"]
}

resource "google_compute_firewall" "allow_wireguard" {
  name    = "allow-wireguard"
  network = "default"
  allow {
    protocol = "udp"
    ports    = ["51820"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["vpn-server"]
}

output "vpn_ip" {
  value = google_compute_instance.vpn_gateway.network_interface.0.access_config.0.nat_ip
}
