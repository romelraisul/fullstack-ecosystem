import os
import json
import requests
import logging
from datetime import datetime

class AgentActivityMonitor:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_AGENT_ACTIVITY_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        self.log_file = os.getenv("LOG_FILE", "logs/activity.log")
        
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        print(f"📈 Performance Monitor Initialized: Targeting {os.getenv('AGENT_NAME')}")

    def log_event(self, event_type, data):
        timestamp = datetime.now().isoformat()
        entry = {
            "ts": timestamp,
            "type": event_type,
            "data": data,
            "version": os.getenv("AGENT_VERSION")
        }
        
        # Log locally
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
        # try:
        #     requests.post(self.endpoint, json=entry, headers={"api-key": self.api_key})
        # except: pass

if __name__ == "__main__":
    monitor = AgentActivityMonitor()
    monitor.log_event("SYSTEM_BOOT", {"status": "operational"})

