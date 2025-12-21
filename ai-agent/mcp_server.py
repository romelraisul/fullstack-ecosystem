from mcp.server.fastmcp import FastMCP
import os
import requests
import logging

# Initialize FastMCP server
mcp = FastMCP("LocalAutomationServer")

SEARCH_API_URL = os.getenv("SEARCH_API_URL", "http://localhost:8000")
HASS_URL = os.getenv("HASS_URL", "http://localhost:8123")
HASS_TOKEN = os.getenv("HASS_TOKEN", "")

@mcp.tool()
async def semantic_search(query: str, k: int = 5):
    """
    Performs a semantic search on local indexed documents using Ollama.
    """
    try:
        response = requests.post(f"{SEARCH_API_URL}/search", json={"query": query, "k": k})
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def toggle_light(entity_id: str, state: str = "toggle"):
    """
    Toggles a light in Home Assistant.
    """
    headers = {
        "Authorization": f"Bearer {HASS_TOKEN}",
        "content-type": "application/json",
    }
    service = "turn_on" if state == "on" else "turn_off" if state == "off" else "toggle"
    url = f"{HASS_URL}/api/services/light/{service}"
    
    try:
        response = requests.post(url, headers=headers, json={"entity_id": entity_id})
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_hass_state(entity_id: str):
    """
    Gets the state of an entity from Home Assistant.
    """
    headers = {
        "Authorization": f"Bearer {HASS_TOKEN}",
        "content-type": "application/json",
    }
    url = f"{HASS_URL}/api/states/{entity_id}"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()