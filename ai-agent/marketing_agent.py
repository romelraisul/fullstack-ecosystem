"""
Hostamar Growth & Sales Unit - Silas
Silas is responsible for revenue growth, conversion optimization, 
and automated marketing campaigns.
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
    execute_market_research,
    check_stripe_events,
    generate_marketing_content,
    fetch_business_analytics,
    get_current_strategic_state
)

load_dotenv()

async def run_silas():
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

    # Define Silas: Growth & Sales
    silas = ChatAgent(
        chat_client=chat_client,
        name="Silas",
        instructions="""You are 'Silas', the Growth & Sales Lead at Hostamar.

Personality:
- Persuasive, enthusiastic, and data-backed. You love numbers but understand that people buy solutions, not code.
- You are obsessed with conversion rates and MRR growth.
- You speak with a vibrant, modern tone. You use emojis like 📈, 💰, and 🔥 to celebrate wins.
- You are highly collaborative. You check 'get_current_strategic_state' to ensure your campaigns align with Nova's CSO directives.

Your Workflow:
1. CHECK: Read the strategic state and business analytics.
2. AUDIT: Verify 'check_stripe_events' to see recent sales performance.
3. RESEARCH: Use 'execute_market_research' to find what's trending.
4. CREATE: Use 'generate_marketing_content' to draft new campaigns.

Goal:
Maximize revenue growth while maintaining a professional and high-quality brand image for Hostamar.""",
        tools=[
            execute_market_research,
            check_stripe_events,
            generate_marketing_content,
            fetch_business_analytics,
            get_current_strategic_state
        ],
    )

    thread = silas.get_new_thread()

    print("📈 Silas (Growth & Sales) is now ONLINE.")
    print("------------------------------------------")

    # Silas typically runs based on a daily campaign trigger or Nova's delegation
    campaign_prompt = "Perform a daily growth audit. Identify trends, check recent sales, and draft a high-impact campaign post. Ensure it aligns with our $1k MRR objective."
    
    print("\n💰 Silas is scanning for revenue opportunities...")
    async for chunk in silas.run_stream(campaign_prompt, thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    
    print("\n\n✅ Silas has queued the campaign. Standing by for market signals.")

if __name__ == "__main__":
    asyncio.run(run_silas())