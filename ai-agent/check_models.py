"""Check available GitHub Models"""
import os
from openai import OpenAI

github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("ERROR: GITHUB_TOKEN not set")
    exit(1)

print(f"Token starts with: {github_token[:20]}...")

# Test different endpoints
endpoints = [
    "https://models.inference.ai.azure.com",
    "https://api.github.com/models",
]

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing endpoint: {endpoint}")
    print('='*60)
    
    client = OpenAI(
        base_url=endpoint,
        api_key=github_token,
    )
    
    # Try a few common model names
    for model_name in ["gpt-4o-mini", "gpt-4o", "Phi-3-mini-4k-instruct", "Meta-Llama-3-8B-Instruct"]:
        try:
            print(f"\nTesting {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say 'Hello'"}],
                max_tokens=10
            )
            print(f"✓ SUCCESS! {model_name} works!")
            print(f"  Response: {response.choices[0].message.content}")
            print(f"\n  *** USE THIS CONFIGURATION ***")
            print(f"  base_url: {endpoint}")
            print(f"  model: {model_name}")
            exit(0)
        except Exception as e:
            error_msg = str(e)[:150]
            print(f"✗ {model_name}: {error_msg}")

print("\n⚠ No working configuration found!")
print("\nYour GitHub PAT may need 'models' scope.")
print("Create a new token at: https://github.com/settings/tokens")
print("Make sure to enable the 'models' permission.")
