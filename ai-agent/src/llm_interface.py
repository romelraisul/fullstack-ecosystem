import os
import json
import logging
import datetime
import time
from dotenv import load_dotenv

# Load configuration
load_dotenv()

class LLMInterface:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")
        self.temperature = float(os.getenv("TEMPERATURE", 0.2))
        self.max_tokens = int(os.getenv("MAX_TOKENS", 1024))
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", 60))
        self.last_request_time = 0
        
        # Validation
        if os.getenv("VALIDATION_MODE") == "ENABLED":
            self._validate_api_key()
            
        print(f"🔐 Security Policy: {os.getenv('AUTH_POLICY')}")
        print(f"🔹 LLM Interface Hardened: {self.model_name} (Limit: {self.rate_limit_rpm} RPM)")

    def _validate_api_key(self):
        """--api-key-validation implementation"""
        if not self.api_key or not self.api_key.startswith("AIza"):
            raise ValueError("❌ CRITICAL: Invalid or missing Google API Key.")
        print("✅ API Key Validation: PASSED")

    def _apply_rate_limit(self):
        """--rate-limit-config implementation"""
        delay = 60.0 / self.rate_limit_rpm
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()

    def generate_response(self, prompt):
        self._apply_rate_limit()
        
        # Mocking actual call for logic validation
        response = {
            "content": f"Verified Response for: {prompt[:20]}",
            "status": "success",
            "provider": "Google/Gemini"
        }
        
        self.log_interaction(prompt, response)
        return response

    def log_interaction(self, prompt, response):
        log_file = os.getenv("LOG_FILE", "logs/api_interactions.log")
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "m": self.model_name,
            "res": response
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    llm = LLMInterface()
    print(llm.generate_response("Operational Test"))