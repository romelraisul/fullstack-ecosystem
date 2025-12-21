import os
import sys
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.exceptions import ClientAuthenticationError

print(f"Python Executable: {sys.executable}")
print("Attempting to invoke Azure CLI...")

try:
    # Try specific CLI credential first to see specific error
    cred = AzureCliCredential()
    token = cred.get_token("https://cognitiveservices.azure.com/.default")
    print(f"✅ AzureCliCredential Success! Token starts with: {token.token[:10]}...")
except Exception as e:
    print(f"❌ AzureCliCredential Failed: {str(e)}")

print("\nAttempting DefaultAzureCredential...")
try:
    cred = DefaultAzureCredential()
    token = cred.get_token("https://cognitiveservices.azure.com/.default")
    print(f"✅ DefaultAzureCredential Success! Token starts with: {token.token[:10]}...")
except ClientAuthenticationError as e:
    print(f"❌ DefaultAzureCredential Failed.")
    # print(e) # Too verbose, keeping it clean
except Exception as e:
    print(f"❌ Unexpected Error: {str(e)}")
