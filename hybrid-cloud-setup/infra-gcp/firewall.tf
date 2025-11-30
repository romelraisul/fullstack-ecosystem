# This file contains the firewall rules for the GCP network.

resource "google_compute_firewall" "allow_tunnel" {
  name    = "allow-wireguard-frp"
  network = "default" # Replace with your VPC network name if not using default

  allow {
    protocol = "udp"
    ports    = ["51820"] # WireGuard
  }

  allow {
    protocol = "tcp"
    ports    = ["7000", "80", "443"] # FRP and Web
  }

  source_ranges = ["0.0.0.0/0"]
}
