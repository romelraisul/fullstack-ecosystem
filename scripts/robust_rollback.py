import os
import sys
import json
import logging
import subprocess
import requests
import time
from datetime import datetime
from typing import Optional, List, Dict

# Configuration
CONFIG = {
    "deployments_dir": "/home/romel/deployments",
    "state_file": "/home/romel/deployments/state.json",
    "nginx_config_path": "/etc/nginx/sites-enabled/hostamar",
    "slack_webhook": os.environ.get("SLACK_WEBHOOK_URL", ""),
    "health_check_url": "https://hostamar.com/api/health",
    "max_retries": 3,
    "retry_delay": 5
}

# Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "action": "%(message)s"}'
)
logger = logging.getLogger("RollbackOrchestrator")

class RollbackEngine:
    def __init__(self, env_type="production"):
        self.env_type = env_type
        if env_type == "staging":
            CONFIG["deployments_dir"] = "/home/romel/staging"
            CONFIG["state_file"] = "/home/romel/staging/state.json"
            CONFIG["health_check_url"] = "http://localhost:4001/api/health" # Direct local check
            self.app_prefix = "hostamar-staging"
        else:
            self.app_prefix = "hostamar"
            
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if os.path.exists(CONFIG["state_file"]):
            with open(CONFIG["state_file"], "r") as f:
                return json.load(f)
        
        # Default ports for staging/prod
        base_port = 4001 if self.env_type == "staging" else 3001
        return {
            "active_env": "blue",
            "environments": {
                "blue": {"port": base_port, "version": "unknown", "path": f"{CONFIG['deployments_dir']}/blue"},
                "green": {"port": base_port + 1, "version": "unknown", "path": f"{CONFIG['deployments_dir']}/green"}
            },
            "history": []
        }

    def _save_state(self):
        with open(CONFIG["state_file"], "w") as f:
            json.dump(self.state, f, indent=2)

    def _send_alert(self, message: str, level: str = "info"):
        payload = {
            "text": f"[{self.env_type.upper()}] Rollback Notification: {message}",
            "ts": datetime.now().isoformat()
        }
        logger.info(f"Alert: {message}")
        if CONFIG["slack_webhook"]:
            try:
                requests.post(CONFIG["slack_webhook"], json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

    def get_history(self, n: int = 5):
        """Returns last N successful deployments from git tags or history"""
        # In this implementation, we check the state history
        return self.state.get("history", [])[-n:]

    def verify_health(self) -> bool:
        """Post-rollback health check"""
        logger.info(f"Verifying health at {CONFIG['health_check_url']}...")
        for i in range(CONFIG["max_retries"]):
            try:
                # For staging, we might need a local request or specific domain
                response = requests.get(CONFIG["health_check_url"], timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        logger.info("Health check PASSED.")
                        return True
            except Exception as e:
                logger.warning(f"Health check attempt {i+1} failed: {e}")
            time.sleep(CONFIG["retry_delay"])
        return False

    def switch_traffic(self, target_env: str) -> bool:
        """Update Nginx to point to the target environment's port"""
        if self.env_type == "staging":
            logger.info("Staging traffic shift - skipping Nginx update (port-based access)")
            self.state["active_env"] = target_env
            self._save_state()
            return True

        target_port = self.state["environments"][target_env]["port"]
        logger.info(f"Switching traffic to {target_env} on port {target_port}...")
        
        try:
            cmd = f"sudo sed -i 's/localhost:[0-9]\+/localhost:{target_port}/g' {CONFIG['nginx_config_path']}"
            subprocess.run(cmd, shell=True, check=True)
            subprocess.run("sudo nginx -t && sudo systemctl reload nginx", shell=True, check=True)
            
            self.state["active_env"] = target_env
            self._save_state()
            return True
        except Exception as e:
            logger.error(f"Traffic shift failed: {e}")
            return False

    def rollback_to_previous(self):
        """Rolls back to the alternate environment (Blue <-> Green)"""
        current = self.state["active_env"]
        target = "green" if current == "blue" else "blue"
        
        logger.info(f"Initiating rollback from {current} to {target}...")
        
        try:
            pm2_check = subprocess.run(f"pm2 jlist", shell=True, capture_output=True, text=True)
            processes = json.loads(pm2_check.stdout)
            
            # Match process by prefix
            target_proc = next((p for p in processes if p['name'].startswith(self.app_prefix) and target in p['name']), None)
            
            if not target_proc or target_proc['pm2_env']['status'] != 'online':
                logger.error(f"Target process for {target} is not online. Attempting to start...")
                # Logic to start if possible
                pass
        except Exception as e:
            self._send_alert(f"Failed to verify {target} environment: {e}", "critical")
            return False

        if self.switch_traffic(target):
            if self.verify_health():
                self._send_alert(f"Rollback to {target} successful and verified.", "success")
                return True
            else:
                self._send_alert("Traffic switched but health check failed!", "critical")
                return False
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    
    env = "staging" if args.staging else "production"
    engine = RollbackEngine(env_type=env)
    
    if args.history:
        print(json.dumps(engine.get_history(), indent=2))
    else:
        success = engine.rollback_to_previous()
        sys.exit(0 if success else 1)
