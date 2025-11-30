"""
Hybrid Cloud Infrastructure Management AI Agent

This agent assists with managing hybrid cloud infrastructure spanning
on-premise Proxmox and Google Cloud Platform resources.
"""

import asyncio
import os
from typing import Annotated

# Set up OpenTelemetry tracing BEFORE importing agent framework
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Initialize OpenTelemetry tracing
resource = Resource(attributes={
    "service.name": "hybrid-cloud-infrastructure-agent"
})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",
)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

from azure.ai.inference.tracing import AIInferenceInstrumentor
AIInferenceInstrumentor().instrument()


# Infrastructure management tools
def check_vm_status(
    vm_id: Annotated[str, "The VM ID to check (e.g., '101' for Proxmox VM)"],
) -> str:
    """Check the status of a virtual machine in the infrastructure."""
    # In a real implementation, this would query Proxmox API or GCP API
    return f"VM {vm_id} is currently running with 4 CPU cores and 8GB RAM allocated."


def list_wireguard_tunnels() -> str:
    """List all WireGuard VPN tunnels configured in the hybrid cloud setup."""
    return """Active WireGuard tunnels:
1. gcp-tunnel (35.225.196.18:51820) - Status: Connected
   - Local: 10.10.0.2/32
   - Remote: 10.10.0.1/24
   - Last handshake: 2 minutes ago"""


def check_ansible_playbook_status(
    playbook_name: Annotated[str, "The name of the Ansible playbook to check"],
) -> str:
    """Check the status or last execution result of an Ansible playbook."""
    playbook_map = {
        "setup-ai-workstation": "Last run: Failed on WinRM authentication. Recommendation: Check Administrator account is enabled and WinRM service is running.",
        "deploy-gateway": "Last run: Successful (2 hours ago). All tasks completed.",
    }
    return playbook_map.get(playbook_name, f"No execution history found for playbook '{playbook_name}'")


def get_infrastructure_overview() -> str:
    """Get a comprehensive overview of the hybrid cloud infrastructure."""
    return """
Hybrid Cloud Infrastructure Overview:
=====================================

On-Premise (Proxmox):
- Server: 192.168.1.83 (pve node)
- CPU: AMD Ryzen 9 9900X (12 cores, 24 threads)
- Memory: 64GB DDR5
- VMs: 1 active (win11-workstation-1, ID: 101)
  - IP: 192.168.1.181
  - Status: Running
  - WinRM: Configured (port 5986)

Cloud (Google Cloud Platform):
- Project: arafat-468807
- Instance: hybrid-cloud-gateway (e2-micro)
- Region: us-central1-a
- Public IP: 35.225.196.18
- WireGuard VPN: Active (UDP 51820)
- Server Public Key: 8agku1antDvg2OjjAj6ERNzqRGIxi1fzNbw5681gr10=

Network:
- VPN Tunnel: gcp-tunnel (Connected)
- WinRM Ports: 5985 (HTTP), 5986 (HTTPS)
- SSH: Port 22 (firewall configured)
"""


def troubleshoot_winrm(issue: Annotated[str, "Description of the WinRM issue"]) -> str:
    """Provide troubleshooting steps for WinRM connectivity issues."""
    return f"""
WinRM Troubleshooting for: {issue}

Common Solutions:
1. Verify Administrator account is enabled:
   PowerShell: net user Administrator /active:yes

2. Check WinRM service is running:
   PowerShell: Get-Service WinRM | Format-List

3. Verify HTTPS listener exists:
   PowerShell: winrm enumerate winrm/config/Listener

4. Enable Basic authentication:
   PowerShell: Set-Item -Path WSMan:\\localhost\\Service\\Auth\\Basic -Value $true

5. Configure TrustedHosts:
   PowerShell: Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value '*' -Force

6. Verify firewall rules:
   PowerShell: Get-NetFirewallRule -DisplayName "*WinRM*"

7. Test local connectivity:
   PowerShell: winrs -r:https://127.0.0.1:5986 -u:Administrator -p:"YOUR_PASSWORD" -ssl ipconfig

If issues persist, check the certificate thumbprint matches in both the listener and Ansible inventory.
"""


async def run_agent():
    """Run the infrastructure management agent."""
    
    # Get Foundry endpoint from environment
    foundry_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not foundry_endpoint:
        print("ERROR: Foundry endpoint not set in environment.")
        print("Please set AZURE_OPENAI_ENDPOINT in your .env file.")
        return

    # Use Azure AD authentication for Foundry
    # Try API key first (if set), otherwise use DefaultAzureCredential
    foundry_key = os.getenv("AZURE_OPENAI_KEY")
    if foundry_key:
        print("Using API key authentication for Foundry.")
        openai_client = AsyncOpenAI(
            base_url=foundry_endpoint,
            api_key=foundry_key,
        )
    else:
        print("Using Azure AD authentication for Foundry.")
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        openai_client = AsyncOpenAI(
            base_url=foundry_endpoint,
            azure_ad_token_provider=token_provider,
        )

    # Get model name from environment (default to gpt-4o-mini)
    model_name = os.getenv("MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_MODEL") or "gpt-4o-mini"

    chat_client = OpenAIChatClient(
        async_client=openai_client,
        model_id=model_name
    )
    
    # Create the infrastructure agent with tools
    agent = ChatAgent(
        chat_client=chat_client,
        name="InfrastructureAgent",
        instructions="""You are an expert infrastructure management assistant for a hybrid cloud setup.
        
Your expertise includes:
- Proxmox virtualization (KVM, LXC containers)
- Google Cloud Platform (GCP) resources
- WireGuard VPN configuration and troubleshooting
- Ansible automation and playbook execution
- Windows Remote Management (WinRM) configuration
- Network troubleshooting and connectivity issues

When users ask questions:
1. Use the available tools to gather current infrastructure status
2. Provide clear, actionable recommendations
3. Include specific commands or configuration snippets when helpful
4. Explain the reasoning behind your suggestions

Be concise but thorough. Focus on practical solutions.""",
        tools=[
            check_vm_status,
            list_wireguard_tunnels,
            check_ansible_playbook_status,
            get_infrastructure_overview,
            troubleshoot_winrm,
        ],
    )
    
    # Create a conversation thread
    thread = agent.get_new_thread()
    
    print("=" * 70)
    print("Hybrid Cloud Infrastructure Management Agent")
    print("=" * 70)
    print("Ask me about your infrastructure, VMs, VPN tunnels, or troubleshooting.")
    print("Type 'quit' or 'exit' to end the session.")
    print("=" * 70)
    print()
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAgent: Goodbye! Your infrastructure is in good hands.")
                break
            
            print("Agent: ", end="", flush=True)
            async for chunk in agent.run_stream(user_input, thread=thread):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\nAgent: Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    asyncio.run(run_agent())
