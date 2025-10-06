"""Basic Locust performance script hitting health endpoint.

Usage (CI headless):
  locust -f perf/locustfile.py --headless -u 25 -r 5 -t 1m --host http://localhost:8000
"""

import time
import uuid

from locust import HttpUser, between, task


def _rand_name(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class QuickHealthUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task
    def health(self):
        self.client.get("/api/v1/health")


class ConversationFlow(HttpUser):
    """Creates a conversation then sends follow-up messages."""

    wait_time = between(0.5, 1.5)
    messages_per_conv = 3

    def on_start(self):
        # Create a conversation with a random agent id (if agents exist endpoint; fallback agent id)
        agent_id = "agent-research"  # fallback
        payload = {
            "agent_id": agent_id,
            "user_message": "Hello agent, summarize performance pipeline.",
            "context": {"topic": "performance"},
        }
        with self.client.post(
            "/api/v1/conversations", json=payload, name="conversation:create", catch_response=True
        ) as resp:
            if resp.status_code == 200:
                try:
                    self.conversation_id = resp.json().get("conversation_id")
                except Exception:
                    resp.failure("Invalid JSON in conversation create")
            else:
                resp.failure(f"Create failed {resp.status_code}")
                self.conversation_id = None

    @task
    def send_messages(self):
        if not getattr(self, "conversation_id", None):
            return
        for i in range(self.messages_per_conv):
            msg = {"content": f"Follow-up message {i}"}
            self.client.post(
                f"/api/v1/conversations/{self.conversation_id}/messages",
                json=msg,
                name="conversation:message",
            )
        # Reset to avoid infinite growth
        self.conversation_id = None
        self.on_start()


class WorkflowExecutionUser(HttpUser):
    """Creates a small workflow then executes it and polls for status."""

    wait_time = between(1.0, 2.0)
    poll_attempts = 5

    def create_workflow(self):
        wf = {
            "name": _rand_name("wf"),
            "description": "Load test workflow",
            "parallel_execution": False,
            "steps": [
                {"name": "step_a", "agent_id": "agent-research", "depends_on": []},
                {"name": "step_b", "agent_id": "agent-research", "depends_on": ["step_a"]},
            ],
        }
        with self.client.post(
            "/api/v1/workflows", json=wf, name="workflow:create", catch_response=True
        ) as r:
            if r.status_code == 200:
                try:
                    return r.json()["workflow_id"]
                except Exception:
                    r.failure("Bad JSON create_workflow")
            else:
                r.failure(f"Workflow create failed {r.status_code}")
        return None

    @task
    def workflow_cycle(self):
        workflow_id = self.create_workflow()
        if not workflow_id:
            return
        # Execute
        exec_id = None
        with self.client.post(
            f"/api/v1/workflows/{workflow_id}/execute", name="workflow:execute", catch_response=True
        ) as r:
            if r.status_code == 200:
                try:
                    exec_id = r.json().get("execution_id")
                except Exception:
                    r.failure("Bad JSON execute")
            else:
                r.failure(f"Execute failed {r.status_code}")
        if not exec_id:
            return
        # Poll
        for _ in range(self.poll_attempts):
            res = self.client.get(f"/api/v1/workflows/executions/{exec_id}", name="workflow:status")
            if res.status_code != 200:
                break
            try:
                status = res.json().get("execution", {}).get("status")
                if status in {"success", "failed"}:
                    break
            except Exception:
                break
            time.sleep(0.5)
