"""Quick diagnostic script to test agent connectivity."""
import os
import asyncio
from infrastructure_agent import ChatAgent, OpenAIChatClient, AsyncOpenAI, check_vm_status

async def test_agent():
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: GITHUB_TOKEN not set")
        return
    
    print("Initializing agent...")
    openai_client = AsyncOpenAI(
        base_url="https://models.github.ai/inference",
        api_key=github_token,
    )
    
    chat_client = OpenAIChatClient(
        async_client=openai_client,
        model_id="gpt-4o-mini"
    )
    
    agent = ChatAgent(
        chat_client=chat_client,
        name="TestAgent",
        instructions="You are a test assistant.",
        tools=[check_vm_status],
    )
    
    print("Sending test query...")
    thread = agent.get_new_thread()
    response = ""
    
    try:
        async for chunk in agent.run_stream("What is 2+2?", thread=thread):
            if chunk.text:
                response += chunk.text
                print(".", end="", flush=True)
        
        print(f"\n\nResponse: {response[:200]}")
        print("\n✓ Agent is working!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
