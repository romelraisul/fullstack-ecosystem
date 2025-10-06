# TLS Certificates

Place production certificates here (mounted read-only into Traefik at /certs).

Required files (self-signed or from CA):

- fullchain.pem
- privkey.pem

## Quick self-signed (DEV ONLY)

```bash
openssl req -x509 -nodes -newkey rsa:4096 -days 365 \
  -keyout privkey.pem -out fullchain.pem \
  -subj "/CN=localhost"
```

Then restart Traefik. For ACME (Let's Encrypt), ensure ports 80/443 are reachable and the email in docker-compose is valid.
