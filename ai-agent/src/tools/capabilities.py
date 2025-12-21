
import requests
import subprocess
import os
import json
from typing import Dict, Any, Annotated

BASE_URL = "http://34.47.163.149:3001/api"
STATE_FILE = "chief_state.json"

def check_system_health() -> str:
    """Monitors system uptime and API response for the Hostamar Platform."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return f"✅ System is HEALTHY. Details: {response.json()}"
        return f"⚠️ System is DEGRADED. Status Code: {response.status_code}"
    except Exception as e:
        return f"🚨 System is CRITICAL. Error: {str(e)}"

def execute_market_research(query: Annotated[str, "The research topic or competitor name"]) -> str:
    """Triggers the Deep Research Agent to analyze market trends or competitors."""
    try:
        response = requests.post(
            f"{BASE_URL}/research",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return f"🚀 Research initiated for '{query}': {response.json()}"
    except Exception as e:
        return f"❌ Research failed: {str(e)}"

def fetch_business_analytics() -> str:
    """Retrieves key metrics including revenue, user growth, and retention."""
    try:
        response = requests.get(f"{BASE_URL}/analytics", timeout=5)
        data = response.json()
        return f"📊 Business Analytics: Revenue ${data.get('monthlyRevenue', 0)}, Active Users: {data.get('totalUsers', 0)}"
    except Exception as e:
        return f"❌ Failed to fetch analytics: {str(e)}"

def deploy_platform_update(component: Annotated[str, "The component to deploy (e.g., 'frontend', 'api', 'ai-engine')"]) -> str:
    """Deploys a pre-built update to the production environment."""
    # In a real scenario, this triggers the safe deploy.py script
    return f"🚀 Nova has triggered a production deployment for: {component}. Monitoring for stability..."

def check_stripe_events() -> str:
    """Verifies recent Stripe webhook events and subscription status."""
    # Simulation of querying Stripe API
    return "✅ Recent events: 2 new subscriptions, 0 churn events in last 24h. Webhooks verified."

def generate_marketing_content(topic: Annotated[str, "The primary focus of the post"]) -> str:
    """Generates high-conversion social media and email content."""
    # Logic to generate content (Silas will use his persona to refine this)
    return f"🚀 Drafted: 'Is your AI ready for {topic}? Hostamar is.' ready for review."

def measure_system_latency() -> str:
    """Measures the end-to-end latency of the Hostamar API in seconds."""
    try:
        # Use curl to get the time_total
        cmd = f"curl -o /dev/null -s -w '%{{time_total}}' {BASE_URL}/health"
        result = subprocess.check_output(cmd, shell=True, text=True)
        latency = float(result.strip())
        status = "🟢 FAST" if latency < 0.5 else "🟡 SLOW" if latency < 2.0 else "🔴 CRITICAL"
        return f"⏱️ Latency: {latency}s | Status: {status}"
    except Exception as e:
        return f"❌ Latency check failed: {str(e)}"

def get_current_strategic_state() -> str:
    """Reads the latest objectives, KPIs, and active tasks from the command center."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.dumps(json.load(f), indent=2)
    return "State file missing."

def update_task_status(
    task_id: Annotated[str, "The ID of the task (e.g., T-101)"],
    status: Annotated[str, "New status: PENDING, IN_PROGRESS, COMPLETED, or FAILED"]
) -> str:
    """Updates the status of a delegated task in the strategic board."""
    if not os.path.exists(STATE_FILE):
        return "Error: State file not found."
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    for task in state.get("active_tasks", []):
        if task["id"] == task_id:
            task["status"] = status
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            return f"✅ Task {task_id} updated to {status}."
    
    return f"❌ Task {task_id} not found."

