import os
import json
import shutil
from datetime import datetime

class ArtifactManager:
    def __init__(self, base_path: str = "G:\\My Drive\\Automations\\registry"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def create_artifact(self, domain: str, version: str, source_dir: str):
        """
        Simulates creating a versioned artifact (e.g., a Docker bundle or code zip).
        """
        artifact_dir = os.path.join(self.base_path, domain, version)
        os.makedirs(artifact_dir, exist_ok=True)
        
        # Simulating artifact bundling
        metadata = {
            "domain": domain,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "source": source_dir
        }
        
        with open(os.path.join(artifact_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"📦 Artifact created: {domain} v{version}")
        return artifact_dir

    def get_latest_version(self, domain: str) -> str:
        domain_path = os.path.join(self.base_path, domain)
        if not os.path.exists(domain_path):
            return "0.0.0"
        versions = sorted(os.listdir(domain_path))
        return versions[-1] if versions else "0.0.0"

    def get_previous_version(self, domain: str) -> str:
        domain_path = os.path.join(self.base_path, domain)
        if not os.path.exists(domain_path):
            return None
        versions = sorted(os.listdir(domain_path))
        if len(versions) < 2:
            return None
        return versions[-2]
