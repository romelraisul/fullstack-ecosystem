# Hybrid Cloud Infrastructure AI Agent

An intelligent AI agent for managing hybrid cloud infrastructure spanning on-premise Proxmox virtualization and Google Cloud Platform resources. Built with **Microsoft Agent Framework** and includes **OpenTelemetry tracing** for observability and a comprehensive **evaluation framework** for performance assessment.

## Features

### 🤖 AI Agent Capabilities
- **VM Management**: Check status, monitor resources for Proxmox virtual machines
- **Network Operations**: List and manage WireGuard VPN tunnels
- **Automation Support**: Query Ansible playbook execution status
- **Infrastructure Overview**: Get comprehensive system status across hybrid cloud
- **Troubleshooting**: Automated WinRM configuration and connectivity diagnostics

### 📊 Observability with Tracing
- **OpenTelemetry Integration**: Full distributed tracing support
- **AI Toolkit Integration**: Automatic trace collection and visualization
- **Performance Monitoring**: Track agent execution, tool calls, and model interactions
- **Debug Support**: Detailed trace data for troubleshooting

### 🎯 Evaluation Framework
- **Response Relevance**: Measures how well responses address infrastructure questions
- **Tool Selection Accuracy**: Verifies correct tool usage for different scenarios
- **Response Coherence**: Assesses response quality and structure
- **Automated Testing**: 10 pre-built test queries covering all agent capabilities

## Architecture

```
ai-agent/
├── infrastructure_agent.py      # Main agent with tracing
├── evaluate_agent.py            # Evaluation framework
├── requirements.txt             # Python dependencies
├── evaluation/
│   ├── test_queries.json       # Test dataset (10 queries)
│   ├── agent_responses.jsonl   # Collected responses
│   └── results/                # Evaluation outputs
└── README.md
```

## Prerequisites

1. **Python 3.8+** installed
2. **GitHub Personal Access Token** with access to GitHub Models
   - Create one at: https://github.com/settings/tokens
   - Requires `read:packages` scope for GitHub Models
3. **AI Toolkit Extension** (for tracing visualization)
   - Install in VS Code: Search for "AI Toolkit"

## Installation

### 1. Install Dependencies

**⚠️ Important**: The `--pre` flag is **required** for Microsoft Agent Framework (currently in preview):

```bash
pip install --pre -r requirements.txt
```

This installs:
- Microsoft Agent Framework with Azure AI integration
- OpenAI SDK for GitHub Models access
- Azure AI Evaluation SDK
- OpenTelemetry tracing components
- Azure AI Inference with OpenTelemetry instrumentation

### 2. (Windows recommended) Create a virtual environment

```powershell
python -m venv "C:\\Users\\romel\\OneDrive\\Documents\\aiauto\\.venv"
"C:\\Users\\romel\\OneDrive\\Documents\\aiauto\\.venv\\Scripts\\python.exe" -m pip install --pre -r "C:\\Users\\romel\\OneDrive\\Documents\\aiauto\\ai-agent\\requirements.txt"
```

The provided runner auto-detects `.venv\\Scripts\\python.exe` if present.

### 3. Set Environment Variables

**On Linux/Mac:**
```bash
export GITHUB_TOKEN='your_github_personal_access_token_here'
```

**On Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN='your_github_personal_access_token_here'
```

**On Windows (Command Prompt):**
```cmd
set GITHUB_TOKEN=your_github_personal_access_token_here
```

## Usage

### Running the Agent

#### 1. Start AI Toolkit Trace Collector

**Before running the agent**, start the trace collector in AI Toolkit:

- Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
- Run: `AI Toolkit: Open Trace Viewer`
- This starts the OTLP collector at `http://localhost:4318`

#### 2. Run the Agent

Option A — VS Code Task (prompts for token):

- Run task: `AI Agent: Run`

Option B — PowerShell runner:

```powershell
powershell -ExecutionPolicy Bypass -File ".\ai-agent\run.ps1" -Mode agent -GithubToken "<your_pat>"
```

The agent will:

- Connect to GitHub Models (using gpt-4.1-mini)
- Initialize OpenTelemetry tracing
- Start an interactive session

**Example Interaction:**

```text
You: What's the current status of my infrastructure?
Agent: Based on the infrastructure overview, here's the current status:

On-Premise (Proxmox):
- Server is running at 192.168.1.83 with AMD Ryzen 9 9900X
- 1 active VM: win11-workstation-1 (ID: 101) at 192.168.1.181

Cloud (Google Cloud Platform):
- Instance: hybrid-cloud-gateway running in us-central1-a
- Public IP: 35.225.196.18
- WireGuard VPN: Active and connected

You: Check VM 101
Agent: VM 101 (win11-workstation-1) is currently running with 4 CPU cores and 8GB RAM allocated.
```

#### 3. View Traces

Open AI Toolkit's Trace Viewer to see:

- Agent execution flow
- Tool calls and their durations
- Model interactions and token usage
- Performance bottlenecks

### Running Evaluation

The evaluation framework automatically collects responses and measures performance.

Option A — VS Code Task (prompts for token):

- Run task: `AI Agent: Evaluate`

Option B — PowerShell runner:

```powershell
powershell -ExecutionPolicy Bypass -File ".\ai-agent\run.ps1" -Mode evaluate -GithubToken "<your_pat>"
```

**What it does:**

1. Runs the agent with 10 test queries (if responses don't exist)
2. Evaluates responses using three metrics:
   - **Response Relevance** (LLM-based)
   - **Response Coherence** (LLM-based)
   - **Tool Selection Accuracy** (code-based)
3. Saves detailed results to `evaluation/results/`

Outputs are written under `evaluation/results/`:

- `evaluation/results/eval_results.jsonl` (row-level)
- `evaluation/results/report.html` (summary)

**Sample Output:**

```text
======================================================================
Evaluation Results
======================================================================

Aggregate Metrics:
----------------------------------------------------------------------
  Relevance Score:          4.2/5.0
  Coherence Score:          4.5/5.0
  Tool Selection Accuracy:  90.00%

----------------------------------------------------------------------

✓ Detailed results saved to: evaluation/results
✓ Row-level data available in: evaluation/results/eval_results.jsonl
```

**To re-run with fresh responses:**

```bash
rm evaluation/agent_responses.jsonl
python evaluate_agent.py
```

## Available Tools

The agent has access to these infrastructure management tools:

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `check_vm_status` | Query VM resources and status | "Check VM 101" |
| `list_wireguard_tunnels` | Show VPN tunnel information | "List all active tunnels" |
| `check_ansible_playbook_status` | Get playbook execution results | "Status of setup-ai-workstation playbook?" |
| `get_infrastructure_overview` | Comprehensive system overview | "Show my infrastructure" |
| `troubleshoot_winrm` | WinRM connectivity diagnostics | "WinRM credentials rejected error" |

## Model Configuration

**Default Model**: `gpt-4.1-mini` (GitHub Models)

- Fast, cost-effective for infrastructure queries
- 1M token context window
- Good balance of quality and speed

**To use a different model**, edit `infrastructure_agent.py`:

```python
chat_client = OpenAIChatClient(
    async_client=openai_client,
    model_id="gpt-4.1"  # or "gpt-5", "o1", etc.
)
```

Available GitHub Models: gpt-4.1, gpt-4.1-mini, gpt-5, gpt-5-mini, o1, o1-mini, and more. See AI Toolkit Model Catalog for full list.

## Tracing Configuration

Tracing is configured to capture:

- **Full prompt and completion content** (enabled via environment variable)
- **Tool call details** (function names, parameters, outputs)
- **Performance metrics** (latency, token counts)

**Tracing endpoint**: `http://localhost:4318/v1/traces` (AI Toolkit OTLP collector)

To disable content recording:
```python
# In infrastructure_agent.py, comment out or remove:
# os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
```

## Evaluation Metrics

### 1. Response Relevance (LLM-based)
- **Range**: 1-5 (higher is better)
- **Measures**: How well the response addresses the user's infrastructure question
- **Evaluator**: Azure AI Evaluation `RelevanceEvaluator`

### 2. Response Coherence (LLM-based)
- **Range**: 1-5 (higher is better)
- **Measures**: Text quality, flow, and readability
- **Evaluator**: Azure AI Evaluation `CoherenceEvaluator`

### 3. Tool Selection Accuracy (Code-based)
- **Range**: 0-1 (accuracy percentage)
- **Measures**: Whether the agent called the expected tool
- **Evaluator**: Custom `ToolSelectionEvaluator`

## Test Dataset

The evaluation includes 10 test queries across 5 categories:

| Category | Count | Examples |
|----------|-------|----------|
| Information Retrieval | 2 | "What's the current status of my infrastructure?" |
| VM Management | 2 | "Check the status of VM 101" |
| Network Management | 2 | "List all active VPN tunnels" |
| Automation Management | 1 | "Status of setup-ai-workstation playbook?" |
| Troubleshooting | 3 | "WinRM credentials were rejected. How do I fix it?" |

Customize test queries by editing `evaluation/test_queries.json`.

## Project Structure

```
ai-agent/
├── infrastructure_agent.py           # Main agent with tools and tracing
│   ├── OpenTelemetry setup
│   ├── Agent initialization
│   ├── 5 infrastructure tools
│   └── Interactive CLI
│
├── evaluate_agent.py                 # Evaluation framework
│   ├── Response collection
│   ├── 3 evaluators (relevance, coherence, tool selection)
│   └── Results aggregation
│
├── evaluation/
│   ├── test_queries.json            # 10 test queries
│   ├── agent_responses.jsonl        # Collected responses (auto-generated)
│   └── results/                     # Evaluation outputs (auto-generated)
│       ├── eval_results.jsonl       # Row-level data
│       └── metrics.json             # Aggregate metrics
│
├── requirements.txt                  # Python dependencies
└── README.md                        # This file
```

## Troubleshooting

### "GITHUB_TOKEN not set"
```bash
# Set your GitHub PAT
export GITHUB_TOKEN='your_token_here'
```

### "Cannot connect to trace collector"
1. Open AI Toolkit in VS Code
2. Run command: `AI Toolkit: Open Trace Viewer`
3. Verify OTLP endpoint is running at `http://localhost:4318`

### "Module not found: agent_framework"
```bash
# Ensure --pre flag is used
pip install --pre agent-framework-azure-ai
```

### "Rate limit exceeded" (GitHub Models)
- GitHub Models have free tier rate limits
- Wait a few minutes or upgrade to paid tier
- Check usage at: https://github.com/settings/billing

### Evaluation fails with "No such file"
```bash
# Ensure test queries exist
ls evaluation/test_queries.json

# If missing, re-create the file from the README examples
```

## Extending the Agent

### Add New Tools

1. Define a Python function with type annotations:
```python
def my_new_tool(
    param: Annotated[str, "Description of parameter"]
) -> str:
    """Tool description."""
    return "result"
```

2. Add to agent's tools list:
```python
agent = ChatAgent(
    chat_client=chat_client,
    tools=[
        check_vm_status,
        my_new_tool,  # Add here
    ],
)
```

### Add Evaluation Metrics

1. Create a custom evaluator class:
```python
class MyCustomEvaluator:
    def __init__(self):
        pass
    
    def __call__(self, *, response: str, **kwargs):
        # Your evaluation logic
        return {"my_metric": score}
```

2. Add to evaluation pipeline:
```python
result = evaluate(
    data=data_file,
    evaluators={
        "relevance": relevance_evaluator,
        "my_metric": MyCustomEvaluator(),
    },
    # ...
)
```

## Related Documentation

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [GitHub Models](https://github.com/marketplace/models)
- [Azure AI Evaluation SDK](https://learn.microsoft.com/azure/ai-studio/how-to/develop/evaluate-sdk)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [AI Toolkit for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio)

## License

This project is part of a hybrid cloud infrastructure setup and follows the licensing of its dependencies.

## Support

For issues specific to:
- **Agent Framework**: https://github.com/microsoft/agent-framework/issues
- **GitHub Models**: https://github.com/github/models-feedback
- **This implementation**: Create an issue in your repository

---

**Note**: This agent is designed for development and testing. For production deployments, implement proper authentication, error handling, and security measures.
