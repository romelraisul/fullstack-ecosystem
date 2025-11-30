# This is the central configuration file for your entire project.
# Fill in the values below before running the automation scripts.

# --- Google Cloud Platform Settings ---
gcp_project_id       = "arafat-468807"
gcp_credentials_file = "C:/Users/romel/OneDrive/Documents/aiauto/arafat-468807-daf06a5538d8.json"

# --- Proxmox Local Server Settings ---
proxmox_api_url      = "https://192.168.1.83:8006/api2/json" # Replace with your Proxmox IP
proxmox_user         = "root@pam"
proxmox_password     = "Rushan01@"

# --- General Settings ---
domain_name          = "your-domain.com" # The domain you will use for your services

# --- Business Modules ---
# List the business models you want to deploy from the blueprint.
# Example: ["rdp", "minio", "webhosting", "vpn", "gameserver"]
business_modules     = ["rdp", "minio"]
