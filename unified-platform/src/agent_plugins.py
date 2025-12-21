import os
import importlib.util
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("PluginLoader")

class PluginLoader:
    def __init__(self, plugins_dir: str):
        self.plugins_dir = plugins_dir
        self.handlers: Dict[str, Any] = {}

    def discover_plugins(self):
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return

        for agent_id in os.listdir(self.plugins_dir):
            agent_path = os.path.join(self.plugins_dir, agent_id)
            if os.path.isdir(agent_path):
                handler_path = os.path.join(agent_path, "handler.py")
                if os.path.exists(handler_path):
                    try:
                        spec = importlib.util.spec_from_file_location(f"agent_{agent_id}", handler_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "handle"):
                            self.handlers[agent_id] = module.handle
                            logger.info(f"Loaded custom handler for agent: {agent_id}")
                    except Exception as e:
                        logger.error(f"Failed to load handler for {agent_id}: {e}")

    def get_handler(self, agent_id: str):
        return self.handlers.get(agent_id)

    def fallback_handle(self, agent_id: str, message: str) -> str:
        return f"Default response from {agent_id}: I received '{message}'"
