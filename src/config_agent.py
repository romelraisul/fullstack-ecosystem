import os
import yaml
import json
import logging
import jsonschema
from typing import Any, Dict

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConfigAgent")

class ConfigurationManager:
    def __init__(self, config_path: str, schema_path: str):
        self.config_path = config_path
        self.schema_path = schema_path
        self.config = {}
        self.schema = {}

    def load_schema(self):
        """Loads the JSON schema definition."""
        try:
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)
            logger.info(f"Schema loaded from {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise

    def load_config(self):
        """Loads configuration from YAML and overrides with Environment Variables."""
        # 1. Load from File
        try:
            with open(self.config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file {self.config_path} not found. Using empty defaults.")
            file_config = {}
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise

        # 2. Override with Environment Variables
        # We look for env vars that match the schema keys
        final_config = file_config.copy()
        
        for key in self.schema.get("properties", {}).keys():
            env_val = os.getenv(key)
            if env_val:
                logger.info(f"Overriding {key} from Environment Variable")
                final_config[key] = env_val

        self.config = final_config

    def validate(self):
        """Validates the current configuration against the schema."""
        try:
            jsonschema.validate(instance=self.config, schema=self.schema)
            logger.info("Configuration validation SUCCESSFUL.")
            return True
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Configuration validation FAILED: {e.message}")
            # In a real agent, you might want to exit or fallback
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def run(self):
        """Main execution flow."""
        logger.info("Starting Configuration Agent...")
        self.load_schema()
        self.load_config()
        if self.validate():
            logger.info("System is ready with valid configuration.")
            logger.debug(f"Loaded Config: {self.config}") # Be careful logging secrets in prod
            return self.config
        else:
            logger.critical("System failed to initialize due to invalid configuration.")
            raise ValueError("Invalid Configuration")

if __name__ == "__main__":
    # Example Usage
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(base_dir, "config", "production.yaml")
    schema_file = os.path.join(base_dir, "schemas", "config.schema.json")

    agent = ConfigurationManager(config_file, schema_file)
    
    # Simulate Environment Variable Override (for testing)
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    try:
        config = agent.run()
        print("\n--- Final Configuration ---")
        for k, v in config.items():
            print(f"{k}: {v}")
    except Exception:
        print("\n--- Configuration Loading Failed ---")
        exit(1)
