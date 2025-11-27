"""
Evaluation script for the Infrastructure Management AI Agent

This script evaluates the agent's performance using multiple metrics:
1. Response Relevance - how well responses address infrastructure questions
2. Tool Call Accuracy - verification of correct tool selection
3. Response Coherence - quality and structure of responses
"""

import os
import json
import asyncio
from typing import Dict, List, Any

from azure.ai.evaluation import evaluate, RelevanceEvaluator, CoherenceEvaluator, OpenAIModelConfiguration


# Custom evaluator for tool call accuracy
class ToolSelectionEvaluator:
    """Custom code-based evaluator to verify correct tool selection."""
    
    def __init__(self):
        pass
    
    def __call__(self, *, response: str, expected_tool: str, **kwargs) -> Dict[str, Any]:
        """
        Evaluate if the agent selected the correct tool.
        
        Args:
            response: The agent's response text
            expected_tool: The expected tool name that should have been called
            
        Returns:
            Dictionary with tool_selection_accuracy score (0 or 1)
        """
        # Check if the expected tool name appears in the response metadata
        # In a real implementation, you would parse tool call logs or trace data
        response_lower = response.lower()
        tool_mentioned = expected_tool.lower().replace("_", " ") in response_lower
        
        return {
            "tool_selection_accuracy": 1 if tool_mentioned else 0,
            "expected_tool": expected_tool,
            "reasoning": f"Expected tool '{expected_tool}' was {'found' if tool_mentioned else 'not found'} in response"
        }


async def collect_agent_responses(queries_file: str, output_file: str):
    """
    Run the agent with test queries and collect responses.
    
    Args:
        queries_file: Path to JSON file containing test queries
        output_file: Path to save responses in JSONL format
    """
    from infrastructure_agent import (
        ChatAgent, OpenAIChatClient, AsyncOpenAI,
        check_vm_status, list_wireguard_tunnels, check_ansible_playbook_status,
        get_infrastructure_overview, troubleshoot_winrm
    )
    
    # Load test queries
    with open(queries_file, 'r') as f:
        test_queries = json.load(f)
    
    # Get Foundry endpoint and key from environment
    foundry_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    foundry_key = os.getenv("AZURE_OPENAI_KEY")
    if not foundry_endpoint or not foundry_key:
        raise ValueError("AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_KEY not set in environment")

    # Initialize agent
    openai_client = AsyncOpenAI(
        base_url=foundry_endpoint,
        api_key=foundry_key,
    )

    chat_client = OpenAIChatClient(
        async_client=openai_client,
        model_id="gpt-4o-mini"  # Update if your Foundry model name differs
    )
    
    agent = ChatAgent(
        chat_client=chat_client,
        name="InfrastructureAgent",
        instructions="You are an expert infrastructure management assistant.",
        tools=[
            check_vm_status,
            list_wireguard_tunnels,
            check_ansible_playbook_status,
            get_infrastructure_overview,
            troubleshoot_winrm,
        ],
    )
    
    # Collect responses
    responses = []
    print(f"Collecting responses for {len(test_queries)} queries...")
    print("This may take several minutes - each query needs agent processing...\n")
    
    for idx, item in enumerate(test_queries, 1):
        query = item["query"]
        print(f"[{idx}/{len(test_queries)}] Processing: {query[:60]}...")
        
        try:
            # Get agent response with timeout
            thread = agent.get_new_thread()
            response_text = ""
            
            # Add progress indicator
            chunk_count = 0
            async for chunk in agent.run_stream(query, thread=thread):
                if chunk.text:
                    response_text += chunk.text
                    chunk_count += 1
                    if chunk_count % 10 == 0:
                        print(".", end="", flush=True)
            
            print(f" ✓ Got response ({len(response_text)} chars)")
            
            # Create evaluation record
            record = {
                "query": query,
                "response": response_text.strip(),
                "expected_tool": item.get("expected_tool", ""),
                "category": item.get("category", "")
            }
            responses.append(record)
            
        except Exception as e:
            print(f" ✗ Error: {str(e)}")
            # Add a placeholder response to continue evaluation
            record = {
                "query": query,
                "response": f"ERROR: {str(e)}",
                "expected_tool": item.get("expected_tool", ""),
                "category": item.get("category", "")
            }
            responses.append(record)
    
    # Save responses in JSONL format (required by evaluate API)
    with open(output_file, 'w') as f:
        for record in responses:
            f.write(json.dumps(record) + '\n')
    
    print(f"\n✓ Collected {len(responses)} responses")
    print(f"✓ Saved to {output_file}")
    return output_file


def run_evaluation(data_file: str, output_path: str = "./evaluation_results"):
    """
    Run comprehensive evaluation using Azure AI Evaluation SDK.
    
    Args:
        data_file: Path to JSONL file with queries and responses
        output_path: Directory to save evaluation results
    """
    print("\n" + "=" * 70)
    print("Starting Infrastructure Agent Evaluation")
    print("=" * 70 + "\n")
    
    # Configure model for LLM-based evaluators.
    # Prefer Foundry (Azure) credentials; fall back to GitHub Models if not present.
    foundry_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    foundry_key = os.getenv("AZURE_OPENAI_KEY")
    foundry_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")

    if foundry_endpoint and foundry_key:
        model_config = OpenAIModelConfiguration(
            type="openai",
            model=foundry_model,
            base_url=foundry_endpoint,
            api_key=foundry_key,
        )
    else:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("No Foundry credentials (AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_KEY) or GITHUB_TOKEN set in environment")

        model_config = OpenAIModelConfiguration(
            type="openai",
            model="gpt-4o-mini",
            base_url="https://models.github.ai/inference",
            api_key=github_token,
        )
    
    # Initialize evaluators
    print("Initializing evaluators...")
    relevance_evaluator = RelevanceEvaluator(model_config=model_config)
    coherence_evaluator = CoherenceEvaluator(model_config=model_config)
    tool_selection_evaluator = ToolSelectionEvaluator()
    
    print("✓ RelevanceEvaluator: Measures how well responses address infrastructure questions")
    print("✓ CoherenceEvaluator: Assesses response structure and readability")
    print("✓ ToolSelectionEvaluator: Verifies correct tool selection\n")
    
    # Run evaluation using the unified evaluate() API
    print("Running evaluation...")
    print(f"Data file: {data_file}")
    print(f"Output path: {output_path}\n")
    
    result = evaluate(
        data=data_file,
        evaluators={
            "relevance": relevance_evaluator,
            "coherence": coherence_evaluator,
            "tool_selection": tool_selection_evaluator,
        },
        evaluator_config={
            "relevance": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "coherence": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "tool_selection": {
                "column_mapping": {
                    "response": "${data.response}",
                    "expected_tool": "${data.expected_tool}"
                }
            }
        },
        output_path=output_path
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("Evaluation Results")
    print("=" * 70 + "\n")

    print("Aggregate Metrics:")
    print("-" * 70)
    metrics = result.get("metrics", {})

    if "relevance" in metrics:
        print(f"  Relevance Score:          {metrics['relevance']:.2f}")
    if "coherence" in metrics:
        print(f"  Coherence Score:          {metrics['coherence']:.2f}")
    if "tool_selection_accuracy" in metrics:
        print(f"  Tool Selection Accuracy:  {metrics['tool_selection_accuracy']:.2%}")

    print("\n" + "-" * 70)
    print(f"\n✓ Detailed results saved to: {output_path}")
    print(f"✓ Row-level data available in: {output_path}/eval_results.jsonl")

    # Generate a simple HTML report for quick viewing
    html_report_path = os.path.join(output_path, "report.html")
    # Ensure output path is a directory. If a file exists with the same
    # name (e.g., from accidental redirection), move it aside and create
    # a proper directory.
    if os.path.exists(output_path) and os.path.isfile(output_path):
        backup_path = output_path + ".bak"
        print(f"WARNING: A file exists at {output_path}. Moving it to {backup_path} and creating directory.")
        try:
            os.replace(output_path, backup_path)
        except Exception as e:
            print(f"Failed to move existing file: {e}")
            raise
    os.makedirs(output_path, exist_ok=True)
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html><head><meta charset='utf-8'>")
        f.write("<title>Infrastructure Agent Evaluation Report</title>")
        f.write("<style>body{font-family:Segoe UI,Arial,sans-serif;margin:2rem;}h1{color:#2563eb;}table{border-collapse:collapse;margin-top:1rem;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f3f4f6;text-align:left;}</style>")
        f.write("</head><body>")
        f.write("<h1>Infrastructure Agent Evaluation Report</h1>")
        f.write("<h2>Aggregate Metrics</h2>")
        f.write("<table><tr><th>Metric</th><th>Value</th></tr>")
        if "relevance" in metrics:
            f.write(f"<tr><td>Relevance Score</td><td>{metrics['relevance']:.2f}</td></tr>")
        if "coherence" in metrics:
            f.write(f"<tr><td>Coherence Score</td><td>{metrics['coherence']:.2f}</td></tr>")
        if "tool_selection_accuracy" in metrics:
            f.write(f"<tr><td>Tool Selection Accuracy</td><td>{metrics['tool_selection_accuracy']:.2%}</td></tr>")
        f.write("</table>")
        f.write("<p>Row-level results are available in <code>eval_results.jsonl</code> in this folder.</p>")
        f.write("</body></html>")

    print(f"\n✓ HTML report generated at: {html_report_path}")

    return result


async def main():
    """Main evaluation workflow."""
    
    # Resolve paths relative to this script so the runner can be launched
    # from the repository root or any other working directory.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    eval_dir = os.path.join(base_dir, "evaluation")
    # File paths
    queries_file = os.path.join(eval_dir, "test_queries.json")
    responses_file = os.path.join(eval_dir, "agent_responses.jsonl")
    results_dir = os.path.join(eval_dir, "results")

    print(f"Using queries file: {queries_file}")
    print(f"Responses file: {responses_file}")
    print(f"Results directory: {results_dir}")
    
    # Step 1: Check if we need to collect responses
    if not os.path.exists(responses_file):
        print("Responses file not found. Collecting fresh responses from agent...\n")
        await collect_agent_responses(queries_file, responses_file)
    else:
        print(f"Using existing responses from: {responses_file}")
        print("(Delete this file to collect fresh responses)\n")
    
    # Step 2: Run evaluation
    result = run_evaluation(responses_file, results_dir)
    
    print("\n" + "=" * 70)
    print("Evaluation Complete!")
    print("=" * 70)
    print("\nTo view detailed results:")
    print(f"  1. Open {results_dir}/eval_results.jsonl for row-level data")
    print(f"  2. Check {results_dir}/ for additional metric files")
    print("\nTo re-run with fresh responses:")
    print(f"  1. Delete {responses_file}")
    print("  2. Run this script again")


if __name__ == "__main__":
    # Prefer Foundry (Azure) credentials. Fall back to GitHub token only
    # if Foundry variables are not present.
    foundry_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    foundry_key = os.getenv("AZURE_OPENAI_KEY")
    github_token = os.getenv("GITHUB_TOKEN")

    if foundry_endpoint and foundry_key:
        print("Using Foundry endpoint from environment.")
    elif github_token:
        print("Found GITHUB_TOKEN in environment; using GitHub Models path.")
    else:
        print("ERROR: No Foundry credentials (AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_KEY) or GITHUB_TOKEN found in environment.")
        print("Set your Foundry credentials in .env or export the variables before running.")
        exit(1)

    asyncio.run(main())
