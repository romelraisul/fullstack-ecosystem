# 🚨 Critical Incident Report: Production Outage - Hostamar Platform

**Date:** December 12, 2025
**Status:** 🔴 ACTIVE OUTAGE
**Severity:** SEV-1 (Critical)
**Affected System:** Production VM (`migrated-vm-asia` / `34.47.163.149`)

---

## 1. Executive Summary
The Hostamar Platform is currently inaccessible via public internet (HTTP/HTTPS) and administrative channels (SSH). Preliminary diagnostics indicate a complete system freeze, likely resulting from resource exhaustion during the recent deployment sequence. As CEO, I assume full accountability for this stability failure.

## 2. Impact Assessment
- **User Impact:** 100% of users cannot access the website or API.
- **Business Impact:** Potential loss of revenue, subscription signups, and trust.
- **Data Integrity:** Database persists on disk; data loss is unlikely but unverified until access is restored.

## 3. Root Cause Analysis (RCA)
Based on system logs and recent operational telemetry, the root cause is identified as **Resource Exhaustion leading to System Freeze**.

*   **Trigger Event:** Execution of a heavy `npm run build` process directly on the production VM (`e2-medium` instance) during the "CEO Deployment" phase.
*   **Contributing Factors:**
    *   **Memory Pressure:** Next.js builds are memory-intensive. Running this alongside PostgreSQL and PM2 likely triggered an OOM (Out of Memory) killer or kernel panic.
    *   **Network Instability:** Persistent SSH timeouts suggests the network stack was already degraded or overwhelmed.
    *   **Deployment Strategy:** Building from source on a constrained production environment (instead of pushing pre-built artifacts) introduced significant load.

## 4. Immediate Resolution Plan (Action Required)
Since the server is unresponsive to network requests (Ping/SSH/HTTP failed), remote recovery is impossible. **Physical** (Virtual) intervention is required.

**Step 1: Hard Reset VM (Google Cloud Console)**
1.  Navigate to **Google Cloud Console** > **Compute Engine**.
2.  Select `migrated-vm-asia`.
3.  Click **RESET** (This reboots the machine like a power cycle).
    *   *Note: Do not "Delete". Just "Reset".*

**Step 2: Verify Recovery**
1.  Wait 2-3 minutes for boot.
2.  Check site access: `http://34.47.163.149`.
3.  If Nginx is up but App is down, SSH in and run:
    ```bash
    pm2 resurrect
    # OR
    cd hostamar-platform && pm2 start ecosystem.config.js --env production
    ```

## 5. Preventative Measures (Strategic Fixes)
To prevent recurrence, we will implement the following:

1.  **CI/CD Pipeline Enforcement:** Strictly prohibit building on production. Use GitHub Actions (as set up in `production-pipeline.yml`) to build artifacts and push *only* the build output (`.next` folder) to the server.
2.  **Resource Swap:** Enable **Swap Space** on the Linux VM (e.g., 4GB swap file) to handle burst memory usage during necessary operations.
    *   *Command:* `sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
3.  **External Monitoring:** Use UptimeRobot or Google Cloud Monitoring to alert us *before* a total freeze (e.g., CPU > 90% alerts).

---
**CEO Statement:** "We prioritize stability above all. This outage highlights a flaw in our manual deployment process which we are correcting immediately through automation and infrastructure hardening."
