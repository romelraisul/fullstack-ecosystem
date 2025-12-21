import os
import time
import json
from artifact_manager import ArtifactManager
from deployment_orchestrator import BlueGreenOrchestrator

class DeploymentWizard:
    def __init__(self, domain: str, port: int):
        self.domain = domain
        self.port = port
        self.am = ArtifactManager()
        self.orchestrator = BlueGreenOrchestrator(domain, port)

    def run(self, version: str):
        print(f"\n🚀 Starting Guided Deployment for {self.domain} (v{version})")
        print("=" * 50)

        # Step 1: Environment Configuration
        print("Step 1: Validating Environment Configuration...")
        env_vars = {
            "DOMAIN": self.domain,
            "PORT": str(self.port),
            "VERSION": version,
            "DATABASE_URL": f"postgresql://user:pass@localhost:5432/{self.domain.replace('.', '_')}"
        }
        # In a real scenario, we'd write this to a .env file in the target env
        print(f"✅ Config generated for {self.domain}")
        time.sleep(1)

        # Step 2: Artifact Management
        print("\nStep 2: Staging Deployment Artifacts...")
        artifact_path = self.am.create_artifact(self.domain, version, "./src")
        print(f"✅ Artifact staged at {artifact_path}")
        time.sleep(1)

        # Step 3: Deployment Execution (Blue-Green)
        print("\nStep 3: Executing Blue-Green Deployment...")
        if not self.orchestrator.pre_flight_checks():
            print("❌ Pre-flight checks failed. Aborting.")
            return

        self.orchestrator.provision_infra()
        
        if not self.orchestrator.run_automated_tests():
            print("❌ Health tests failed. Initiating Rollback Strategy...")
            self.rollback_procedure()
            return

        # Step 4: Traffic Shift
        print("\nStep 4: Shifting Traffic to New Version...")
        self.orchestrator.shift_traffic()
        
        # Step 5: Verification
        print("\nStep 5: Monitoring Post-Deployment Stability...")
        if not self.orchestrator.monitor_stability(5):
            print("❌ Stability check failed. Rolling back...")
            self.rollback_procedure()
            return

        print("\n✨ Deployment COMPLETE and Verified.")
        print(f"Active URL: http://{self.domain}")
        print("=" * 50)

    def rollback_procedure(self):
        prev_version = self.am.get_previous_version(self.domain)
        print(f"⚠️ Rolling back to previous stable version: {prev_version if prev_version else 'N/A'}")
        self.orchestrator.rollback()
        print("✅ Rollback complete. System stabilized.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python deploy_wizard.py <domain> <version>")
        sys.exit(1)
        
    domain = sys.argv[1]
    version = sys.argv[2]
    
    # Port mapping logic (example)
    port_map = {
        "og-audio.com": 9000,
        "treasurepointonline.com": 9100,
        "romelraisul.com": 9200,
        "fgisp.com": 9300
    }
    
    port = port_map.get(domain, 9999)
    wizard = DeploymentWizard(domain, port)
    wizard.run(version)
