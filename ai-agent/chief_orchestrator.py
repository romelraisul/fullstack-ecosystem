"""
Hostamar Strategic Command Center - Nova (CSO)
"""
import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from tools.capabilities import (
    check_system_health,
    execute_market_research,
    fetch_business_analytics,
    deploy_platform_update,
    get_current_strategic_state,
    update_task_status
)

load_dotenv()

async def run_nova():
    # Setup Local Ollama Client
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
    model_name = os.getenv("OLLAMA_MODEL", "llama3")
    
    print(f"🚀 Nova (CSO) connecting to Local Ollama at {ollama_host}")
    
    openai_client = AsyncOpenAI(
        base_url=ollama_host,
        api_key="ollama"
    )

    chat_client = OpenAIChatClient(
        async_client=openai_client,
        model_id=model_name
    )

    nova = ChatAgent(
        chat_client=chat_client,
        name="Nova",
        instructions="Analyze business strategy and monitor system health.",
        tools=[check_system_health, fetch_business_analytics, update_task_status],
    )

    thread = nova.get_new_thread()
    print("🌌 Nova (CSO) is now ONLINE.")

    try:
        while True:
            print("\n🔍 Cycle Start...")
            async for chunk in nova.run_stream("Audit system and revenue.", thread=thread):
                if chunk.text: print(chunk.text, end="", flush=True)
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Standby.")

if __name__ == "__main__":
    asyncio.run(run_nova())
