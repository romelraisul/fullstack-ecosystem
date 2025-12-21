import os
import requests
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("LLMClient")

class OllamaClient:
    def __init__(self):
        self.endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
        self.model = "gptoss"
        self.api_key = os.getenv("OLLAMA_API_KEY")

    def generate(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Error: No response from model.")
        except Exception as e:
            logger.error(f"Ollama API Error: {e}")
            return f"Service Unavailable: {str(e)}"

llm = OllamaClient()
