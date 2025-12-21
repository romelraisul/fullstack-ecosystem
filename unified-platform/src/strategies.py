import random
from typing import Dict, Any
from rag_engine import rag_engine
from llm_client import llm

class BehaviorStrategy:
    def execute(self, agent_id: str, content: str) -> str:
        raise NotImplementedError()

class ResearchStrategy(BehaviorStrategy):
    def execute(self, agent_id: str, content: str) -> str:
        query = rag_engine.sanitize_query(content)
        results = rag_engine.search(query)
        
        context = ""
        if results and results[0]["score"] > 0.1:
            context = "\nRelevant Knowledge:\n" + \
                      "\n".join([f"- {r['doc']['content']}" for r in results])
        
        system_prompt = f"You are Research Agent {agent_id}. Use the following context if relevant: {context}"
        return llm.generate(content, system_prompt)

class CodingStrategy(BehaviorStrategy):
    def execute(self, agent_id: str, content: str) -> str:
        system_prompt = f"You are Coding Agent {agent_id}. Provide concise, clean, and bug-free code snippets."
        return llm.generate(content, system_prompt)

class DefaultStrategy(BehaviorStrategy):
    def execute(self, agent_id: str, content: str) -> str:
        system_prompt = f"You are Agent {agent_id}. Be professional and helpful."
        return llm.generate(content, system_prompt)

STRATEGIES: Dict[str, BehaviorStrategy] = {
    "research": ResearchStrategy(),
    "coding": CodingStrategy(),
    "default": DefaultStrategy()
}

def get_strategy(category: str) -> BehaviorStrategy:
    return STRATEGIES.get(category, STRATEGIES["default"])

