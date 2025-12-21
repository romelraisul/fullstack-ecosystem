import asyncio
import logging
import uuid
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from repository import WorkflowRepository
from persistence import WorkflowModel, WorkflowExecutionModel

logger = logging.getLogger("WorkflowEngine")

class WorkflowCycleError(Exception):
    pass

class WorkflowEngine:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo

    def resolve_dependencies(self, spec: Dict[str, Any]) -> List[Dict]:
        """
        Topological Sort using Kahn's Algorithm with Cycle Detection.
        Expects steps to have 'id' and 'depends_on' (list of IDs).
        """
        steps = spec.get("steps", [])
        adj = {step["id"]: step.get("depends_on", []) for step in steps}
        in_degree = {step["id"]: 0 for step in steps}
        
        for step_id in adj:
            for dep in adj[step_id]:
                if dep in in_degree:
                    in_degree[step_id] += 1

        queue = [step_id for step_id in in_degree if in_degree[step_id] == 0]
        sorted_ids = []

        while queue:
            u = queue.pop(0)
            sorted_ids.append(u)
            
            # Find nodes that depend on u
            for step_id, deps in adj.items():
                if u in deps:
                    in_degree[step_id] -= 1
                    if in_degree[step_id] == 0:
                        queue.append(step_id)

        if len(sorted_ids) != len(steps):
            raise WorkflowCycleError("Cycle detected in workflow dependencies or invalid references.")

        # Map back to full step objects
        step_map = {step["id"]: step for step in steps}
        return [step_map[sid] for sid in sorted_ids]

    async def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]):
        logger.info(f"Executing step: {step.get('id')} ({step.get('name')})")
        # Placeholder for actual tool/agent execution
        await asyncio.sleep(step.get("delay", 0.5))
        return {"status": "success", "output": f"Step {step.get('id')} finished.", "ts": time.time()}

    async def run_workflow(self, wf_id: str):
        # 1. Start execution
        wf = self.repo.session.query(WorkflowModel).filter(WorkflowModel.id == wf_id).first()
        if not wf:
            logger.error(f"Workflow {wf_id} not found")
            return

        self.repo.update_status(wf_id, "running")
        
        # Create execution record
        exec_id = str(uuid.uuid4())
        execution = WorkflowExecutionModel(
            id=exec_id,
            workflow_id=wf_id,
            state_json={"steps_completed": []},
            started_at=datetime.utcnow()
        )
        self.repo.session.add(execution)
        self.repo.session.commit()

        steps = self.resolve_dependencies(wf.spec_json)
        context = {}
        
        try:
            for step in steps:
                result = await self.execute_step(step, context)
                context[step["id"]] = result
                
                # Update execution state
                execution.state_json = dict(execution.state_json)
                execution.state_json["steps_completed"].append({"id": step["id"], "result": result})
                self.repo.session.commit()

            self.repo.update_status(wf_id, "success")
            execution.finished_at = datetime.utcnow()
            self.repo.session.commit()
            logger.info(f"Workflow {wf_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Workflow {wf_id} failed: {e}")
            self.repo.update_status(wf_id, "failed")
            execution.finished_at = datetime.utcnow()
            self.repo.session.commit()
