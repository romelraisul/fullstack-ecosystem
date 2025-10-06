"""
Test health endpoint functionality
"""

import asyncio
import time
from datetime import datetime

import httpx
import pytest


class TestHealthEndpoint:
    """Test the /health endpoint"""

    @pytest.fixture
    async def client(self):
        """Create test client with proper timeout"""
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(
            base_url="http://localhost:8000", timeout=timeout, verify=False
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists and returns 200"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint returns proper JSON structure"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()

            # Check required fields
            assert "status" in data
            assert "service" in data
            assert "version" in data
            assert "timestamp" in data

            # Check data types
            assert isinstance(data["status"], str)
            assert isinstance(data["service"], str)
            assert isinstance(data["version"], str)
            assert isinstance(data["timestamp"], str)
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_timestamp_format(self, client):
        """Test that timestamp is in ISO format"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()
            timestamp = data["timestamp"]

            # Should be able to parse ISO timestamp
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                pytest.fail("Timestamp is not in valid ISO format")
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_diagnostics(self, client):
        """Test that diagnostics information is included"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()

            # Check for diagnostics if present
            if "diagnostics" in data:
                diagnostics = data["diagnostics"]
                assert isinstance(diagnostics, dict)

                # Common diagnostic fields
                expected_fields = ["ollama_status", "auto_recovery", "available_models"]

                for field in expected_fields:
                    if field in diagnostics:
                        assert diagnostics[field] is not None
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client):
        """Test that health endpoint responds quickly"""
        try:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to ms

            assert response.status_code == 200
            assert response_time < 5000  # Should respond within 5 seconds
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_content_type(self, client):
        """Test that health endpoint returns JSON content type"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_multiple_calls(self, client):
        """Test that health endpoint is consistent across multiple calls"""
        try:
            responses = []

            # Make 3 consecutive calls
            for _ in range(3):
                response = await client.get("/health")
                assert response.status_code == 200
                responses.append(response.json())
                await asyncio.sleep(0.1)  # Small delay between calls

            # Check that service and version are consistent
            for i in range(1, len(responses)):
                assert responses[i]["service"] == responses[0]["service"]
                assert responses[i]["version"] == responses[0]["version"]
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_status_values(self, client):
        """Test that status field contains valid values"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()
            status = data["status"]

            # Status should be one of expected values
            valid_statuses = ["healthy", "degraded", "unhealthy", "critical"]
            assert status in valid_statuses
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_no_sensitive_data(self, client):
        """Test that health endpoint doesn't expose sensitive information"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            response_text = response.text.lower()

            # Should not contain sensitive keywords
            sensitive_keywords = [
                "password",
                "secret",
                "key",
                "token",
                "credential",
                "api_key",
                "private",
            ]

            for keyword in sensitive_keywords:
                assert keyword not in response_text
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")

    @pytest.mark.asyncio
    async def test_health_endpoint_cors_headers(self, client):
        """Test that health endpoint includes proper CORS headers"""
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            # Check for CORS headers if configured
            headers = response.headers
            if "access-control-allow-origin" in headers:
                assert headers["access-control-allow-origin"] is not None
        except httpx.RemoteProtocolError:
            pytest.skip("Server not running or connection issue")
