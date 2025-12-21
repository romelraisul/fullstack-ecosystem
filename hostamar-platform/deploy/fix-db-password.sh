#!/bin/bash
# Ignore errors if DB/User exists
sudo -u postgres psql -c "CREATE DATABASE hostamar;" || true
sudo -u postgres psql -c "CREATE USER hostamar_user WITH PASSWORD 'hostamar_secure_2025';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hostamar TO hostamar_user;"
sudo -u postgres psql -c "ALTER DATABASE hostamar OWNER TO hostamar_user;"