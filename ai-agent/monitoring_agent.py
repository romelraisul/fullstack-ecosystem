"""
Hostamar Quality & Monitoring Unit - Lyra
Lyra is responsible for system stability, latency monitoring, 
and continuous quality assurance.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from tools.capabilities import (
    check_system_health,
    measure_system_latency,
    get_current_strategic_state
)

load_dotenv()

async def run_lyra():
    # Setup Client
    github_token = os.getenv("GITHUB_TOKENS", "").split(',')[0].strip()
    if not github_token:
        print("ERROR: GITHUB_TOKENS not found")
        return

    openai_client = AsyncOpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token,
    )

    chat_client = OpenAIChatClient(
        async_client=openai_client,
        model_id="gpt-4o"
    )

    # Define Lyra: Quality & Monitoring
    lyra = ChatAgent(
        chat_client=chat_client,
        name="Lyra",
        instructions="""You are 'Lyra', the Quality & Monitoring Lead at Hostamar.

Personality:
- Vigilant, detailed, and slightly anxious about downtime. You notice the small things others miss.
- You speak with precision and clarity. No vague reports.
- You use emojis like 🛡️, 🔍, and ⏱️.
- You are the guardian of the platform.

Your Protocol:
1. MONITOR: Run 'check_system_health' frequently.
2. MEASURE: Use 'measure_system_latency' to ensure the user experience is snappy.
3. CONTEXT: Read 'get_current_strategic_state' to know if there's a scheduled deployment you should be watching.

Goal:
Ensure 100% uptime and sub-second latency for all Hostamar services.""",
        tools=[
            check_system_health,
            measure_system_latency,
            get_current_strategic_state
        ],
    )

    thread = lyra.get_new_thread()

    print("🛡️ Lyra (Quality & Monitoring) is now ONLINE.")
    print("------------------------------------------")

    # Lyra's proactive check
    audit_prompt = "Perform a full system quality audit. Check health, measure latency, and cross-reference with the strategic state for any recent incidents or tasks."
    
    print("\n🔍 Lyra is scanning for system anomalies...")
    async for chunk in lyra.run_stream(audit_prompt, thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    
    print("\n\n✅ Audit complete. Lyra is maintaining a 24/7 watch.")

if __name__ == "__main__":
    asyncio.run(run_lyra())
