
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

STATE_FILE = "chief_state.json"

class StateManager:
    def __init__(self):
        self.state_file = STATE_FILE
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._default_state()
        return self._default_state()

    def _default_state(self) -> Dict:
        return {
            "strategic_objectives": [
                {"id": 1, "goal": "Deploy Hostamar Platform", "status": "COMPLETED", "progress": 100},
                {"id": 2, "goal": "Integrate AI Capabilities", "status": "IN_PROGRESS", "progress": 80},
                {"id": 3, "goal": "Achieve $1k MRR", "status": "PENDING", "progress": 0}
            ],
            "kpis": {
                "system_uptime": 100.0,
                "api_health": "HEALTHY",
                "active_users": 0,
                "revenue": 0.0
            },
            "active_tasks": [
                {"id": "T-101", "agent": "SalesBot-Alpha", "description": "Verify Stripe Webhooks", "status": "PENDING"},
                {"id": "T-102", "agent": "DevUnit-Beta", "description": "Monitor Video API Latency", "status": "PENDING"},
                {"id": "T-103", "agent": "Strategos-Prime", "description": "Daily Competitor Analysis", "status": "PENDING"}
            ],
            "operational_logs": [],
            "last_updated": datetime.now().isoformat()
        }

    def save_state(self):
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def log_operation(self, action: str, status: str, details: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "details": details
        }
        self.state["operational_logs"].insert(0, log_entry)
        # Keep logs manageable
        self.state["operational_logs"] = self.state["operational_logs"][:100]
        self.save_state()

    def update_kpi(self, key: str, value: any):
        self.state["kpis"][key] = value
        self.save_state()

    def get_objectives(self) -> List[Dict]:
        return self.state["strategic_objectives"]
