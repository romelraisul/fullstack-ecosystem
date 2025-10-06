# Security & Secrets Hardening Guide

This document outlines how to properly manage, rotate, and inject secrets for the fullstack + autogen ecosystem.

## 1. NEVER Commit Real Secrets
Placeholders like `CHANGEME_...` are **signals** to load real values at runtime. Do not replace them directly in versioned files.

## 2. Secret Categories
| Category | Examples | Recommended Store |
|----------|----------|-------------------|
| Database | POSTGRES_PASSWORD, DATABASE_URL | Docker secrets / Vault / Azure Key Vault |
| Caches & Queues | REDIS_PASSWORD, RABBITMQ_PASS | Docker secrets / Vault |
| LLM / AI | OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_KEY | Vault / Cloud Secret Manager |
| Monitoring | GRAFANA_ADMIN_PASSWORD | Docker secrets / Vault |
| App Auth | JWT_SECRET, SESSION_SECRET | Vault / KMS-backed rotation |

## 3. Local Development Patterns
Create an untracked file: `.secrets/dev.env`
```env
POSTGRES_PASSWORD=local_dev_pg_pw
REDIS_PASSWORD=local_dev_redis_pw
GRAFANA_ADMIN_PASSWORD=admin12345
RABBITMQ_PASS=dev_rabbit_pw
OPENAI_API_KEY=sk-local-example
```
Add to `.gitignore`:
```
.secrets/
**/dev.env
```
Reference it in `docker-compose.override.yml`:
```yaml
services:
  autogen-backend:
    env_file:
      - ./.secrets/dev.env
```

## 4. Production Secret Injection (Options)
### A. Docker Secrets (Swarm / Compose v3+)
Create secrets:
```bash
echo -n 'prod-super-pg-pass' | docker secret create pg_password -
```
Use in compose:
```yaml
services:
  autogen-postgres:
    secrets:
      - pg_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
secrets:
  pg_password:
    external: true
```
Then modify entrypoint or use images supporting `_FILE` pattern.

### B. Vault / Cloud Secret Manager
- Inject via sidecar or environment expansion script.
- Prefer short-lived tokens; rotate keys automatically.

### C. CI/CD Injection
In GitHub Actions / Azure DevOps pipelines:
```yaml
- name: Export secrets
  run: |
    echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> $GITHUB_ENV
    echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> $GITHUB_ENV
```
Then build with `--build-arg` or runtime `--env-file`.

## 5. Rotation Policy
| Secret | Rotate | Method |
|--------|--------|--------|
| DB Password | 90 days | Managed password rotation tool |
| Redis Password | 90 days | Coordinated drain + restart |
| API Keys (LLM) | 60 days | Use dual-key overlap deployment |
| JWT / Session Secrets | 30–60 days | Key ring + kid header rotation |

## 6. Observability of Secrets Usage
Add metrics/log auditing for:
- Unexpected auth failures (could indicate brute force)
- Sudden key usage spike
- Expired key access attempts

## 7. Secure Runtime Baseline
- Drop unnecessary Linux capabilities (already done for some nginx service)
- Run containers as non-root (adjust Dockerfiles where possible)
- Use read-only root FS where practical
- Enable network segmentation (separate internal vs gateway networks if needed)

## 8. Future Enhancements
- Add `trivy` or `grype` scan in CI
- SOPS + GitOps for encrypted secret specs
- mTLS between internal services
- HashiCorp Boundary / cloud native identity for service-to-service auth

## 9. Quick Checklist Before Production
- [ ] No plaintext secrets in repo
- [ ] All runtime secrets injected via environment or secret manager
- [ ] Rotation calendar established & automated
- [ ] Access to secret manager audited
- [ ] Incident response playbook includes secret revocation steps

## 10. Emergency Secret Rotation Steps (Playbook)
1. Identify compromised category (e.g., Redis password leak).
2. Issue new secret in manager.
3. Deploy rolling updates using new secret (support dual secret window if possible).
4. Invalidate old secret.
5. Force reconnection (restart dependent services).
6. Audit access/log anomalies for 24h.

---
Questions or need automation scripts for secret rotation? Add a task and we can scaffold it.
