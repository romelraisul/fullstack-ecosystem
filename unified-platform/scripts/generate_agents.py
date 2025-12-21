from ruamel.yaml import YAML
import os

def generate_agents():
    agents = []
    categories = ["research", "coding", "data", "content", "ops", "architecture", "business", "legal", "security"]
    
    # Generate 81 agents (9 categories * 9 agents each)
    for i, cat in enumerate(categories):
        for j in range(1, 10):
            agent_id = f"{cat}_{j}"
            agent = {
                "id": agent_id,
                "name": f"{cat.capitalize()} Agent {j}",
                "category": cat,
                "capabilities": [cat, "general_purpose"],
                "strategy": "default",
                "status": "active",
                "version": "1.0.0",
                "metadata": {
                    "description": f"Specialized {cat} agent number {j}",
                    "model": "gpt-4o-mini"
                }
            }
            agents.append(agent)
    
    config = {"agents": agents}
    
    output_path = os.path.join(os.path.dirname(__file__), "../config/agents.yaml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(output_path, "w") as f:
        yaml.dump(config, f)
    
    print(f"Generated {len(agents)} agents in {output_path}")

if __name__ == "__main__":
    generate_agents()
