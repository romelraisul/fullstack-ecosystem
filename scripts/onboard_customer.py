import os
import yaml
import logging
from deployment_orchestrator import BlueGreenOrchestrator

# Setup Logging
logger = logging.getLogger("Onboarding")

class CustomerOnboarder:
    def __init__(self, domain: str, base_port: int):
        self.domain = domain
        self.base_port = base_port
        self.staging_port = base_port + 50 # Offset for staging

    def provision_staging(self):
        logger.info(f"Provisioning staging infrastructure for {self.domain} on port {self.staging_port}...")
        # Create staging docker-compose
        config = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest", # Placeholder
                    "ports": [f"{self.staging_port}:80"],
                    "environment": ["ENV=staging"]
                }
            }
        }
        os.makedirs(f"G:\\My Drive\\Automations\\deployments\\{self.domain}\\staging", exist_ok=True)
        with open(f"G:\\My Drive\\Automations\\deployments\\{self.domain}\\staging\\docker-compose.yaml", "w") as f:
            yaml.dump(config, f)
        
        logger.info(f"Staging infra manifest created for {self.domain}.")

    def generate_runbook(self):
        runbook = f"""
# Deployment Runbook: {self.domain}
## 1. Pre-flight Checks
- Verify Port {self.base_port} (Blue) and {self.base_port+1} (Green) availability.
- Check Prometheus Scrape Targets.

## 2. Traffic Shifting Strategy
- Uses Nginx upstream weighted rotation.
- Shift 10% -> 50% -> 100% via config reload.

## 3. Communication Plan
- Internal: Slack #deployments
- External: Status Page updated via API on successful shift.

## 4. Rollback
- Automated trigger: 5xx errors > 1% over 60s.
- Manual trigger: `python deployment_orchestrator.py --rollback {self.domain}`
"""
        with open(f"G:\\My Drive\\Automations\\deployments\\{self.domain}\\RUNBOOK.md", "w") as f:
            f.write(runbook)
        logger.info(f"Runbook generated for {self.domain}.")

if __name__ == "__main__":
    # Point 107+: Staging and New User Onboarding
    new_customers = [
        {"domain": "fgisp.com", "port": 9300},
        {"domain": "new-user-1.com", "port": 9400}
    ]
    
    onboarder = None
    for c in new_customers:
        onboarder = CustomerOnboarder(c["domain"], c["port"])
        onboarder.provision_staging()
        onboarder.generate_runbook()
        
        # Deploy to production after staging setup
        orchestrator = BlueGreenOrchestrator(c["domain"], c["port"])
        orchestrator.deploy()
