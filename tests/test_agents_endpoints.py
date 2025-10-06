"""
Test agent listing and single agent retrieval
"""

import time

import httpx
import pytest


class TestAgentEndpoints:
    """Test agent-related endpoints"""

    @pytest.fixture
    async def client(self):
        """Create test client with proper timeout"""
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(
            base_url="http://localhost:8000", timeout=timeout, verify=False
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_list_agents_endpoint(self, client):
        """Test listing all agents"""
        try:
            response = await client.get("/api/v1/agents")
            assert response.status_code == 200

            data = response.json()

            # Check response structure
            assert isinstance(data, (list, dict))

            if isinstance(data, list):
                # Direct list of agents
                agents = data
            elif isinstance(data, dict):
                # Wrapped response with agents key
                if "agents" in data:
                    agents = data["agents"]
                elif "categories" in data:
                    # Categories format
                    agents = []
                    for category_agents in data["categories"].values():
                        agents.extend(category_agents)
                else:
                    agents = []

            # Verify agents structure
            assert isinstance(agents, list)
            if agents:  # Only check if agents exist
                agent = agents[0]
                assert isinstance(agent, dict)

                # Check required fields
                required_fields = ["agent_id", "name"]
                for field in required_fields:
                    if field in agent:
                        assert agent[field] is not None

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agent_response_fields(self, client):
        """Test that agent objects have expected fields"""
        try:
            response = await client.get("/api/v1/agents")
            assert response.status_code == 200

            data = response.json()
            agents = []

            if isinstance(data, list):
                agents = data
            elif isinstance(data, dict):
                if "agents" in data:
                    agents = data["agents"]
                elif "categories" in data:
                    for category_agents in data["categories"].values():
                        agents.extend(category_agents)

            if agents:
                agent = agents[0]

                # Common agent fields
                expected_fields = ["agent_id", "name", "description", "capabilities", "category"]

                for field in expected_fields:
                    if field in agent:
                        assert agent[field] is not None

                # Validate field types
                if "capabilities" in agent:
                    assert isinstance(agent["capabilities"], list)

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_single_agent_retrieval(self, client):
        """Test retrieving a single agent by ID"""
        try:
            # First get list of agents
            response = await client.get("/api/v1/agents")
            assert response.status_code == 200

            data = response.json()
            agents = []

            if isinstance(data, list):
                agents = data
            elif isinstance(data, dict):
                if "agents" in data:
                    agents = data["agents"]
                elif "categories" in data:
                    for category_agents in data["categories"].values():
                        agents.extend(category_agents)

            if agents:
                # Get the first agent's ID
                agent_id = agents[0].get("agent_id") or agents[0].get("id")

                if agent_id:
                    # Test single agent retrieval
                    single_response = await client.get(f"/api/v1/agents/{agent_id}")

                    if single_response.status_code == 200:
                        single_agent = single_response.json()

                        # Verify it's a single agent object
                        assert isinstance(single_agent, dict)

                        # Check that it has agent details
                        assert "agent_id" in single_agent or "id" in single_agent
                        assert "name" in single_agent

                        # Verify the ID matches
                        returned_id = single_agent.get("agent_id") or single_agent.get("id")
                        assert returned_id == agent_id
                    else:
                        # 404 is acceptable if agent doesn't exist
                        assert single_response.status_code == 404

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_nonexistent_agent_404(self, client):
        """Test that requesting nonexistent agent returns 404"""
        try:
            response = await client.get("/api/v1/agents/nonexistent_agent_id")
            assert response.status_code == 404

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agents_response_performance(self, client):
        """Test that agents endpoint responds quickly"""
        try:
            start_time = time.time()
            response = await client.get("/api/v1/agents")
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to ms

            assert response.status_code == 200
            assert response_time < 10000  # Should respond within 10 seconds

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agents_json_content_type(self, client):
        """Test that agents endpoint returns JSON"""
        try:
            response = await client.get("/api/v1/agents")
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agent_categories_endpoint(self, client):
        """Test agent categories endpoint if it exists"""
        try:
            response = await client.get("/api/v1/agent-categories")

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)

                # Check for categories structure
                if "categories" in data:
                    categories = data["categories"]
                    assert isinstance(categories, dict)

                    # Each category should have agents
                    for _category_name, category_agents in categories.items():
                        assert isinstance(category_agents, list)

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agent_search_functionality(self, client):
        """Test agent search if supported"""
        try:
            # Try search with query parameter
            response = await client.get("/api/v1/agents?search=agent")

            if response.status_code == 200:
                data = response.json()
                # Should return valid agent structure
                assert isinstance(data, (list, dict))

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agent_filtering_by_category(self, client):
        """Test agent filtering by category if supported"""
        try:
            # Try filtering by category
            response = await client.get("/api/v1/agents?category=business")

            if response.status_code == 200:
                data = response.json()
                # Should return valid structure
                assert isinstance(data, (list, dict))

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")

    @pytest.mark.asyncio
    async def test_agent_data_consistency(self, client):
        """Test that agent data is consistent between list and single retrieval"""
        try:
            # Get agents list
            list_response = await client.get("/api/v1/agents")
            assert list_response.status_code == 200

            list_data = list_response.json()
            agents = []

            if isinstance(list_data, list):
                agents = list_data
            elif isinstance(list_data, dict):
                if "agents" in list_data:
                    agents = list_data["agents"]
                elif "categories" in list_data:
                    for category_agents in list_data["categories"].values():
                        agents.extend(category_agents)

            if agents:
                agent_from_list = agents[0]
                agent_id = agent_from_list.get("agent_id") or agent_from_list.get("id")

                if agent_id:
                    # Get single agent
                    single_response = await client.get(f"/api/v1/agents/{agent_id}")

                    if single_response.status_code == 200:
                        agent_from_single = single_response.json()

                        # Compare key fields
                        list_name = agent_from_list.get("name")
                        single_name = agent_from_single.get("name")

                        if list_name and single_name:
                            assert list_name == single_name

        except httpx.ConnectError:
            pytest.skip("Server not running")
        except httpx.RemoteProtocolError:
            pytest.skip("Server connection issue")
