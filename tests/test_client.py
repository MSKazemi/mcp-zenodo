"""
Tests for the MCP Zenodo client implementation.
"""

import pytest
from server.client import MCPZenodoClient
from models.request import MCPRequest

@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = MCPZenodoClient()
    assert client is not None
    assert client.auth_root is not None
    assert client.sampling_root is not None

@pytest.mark.asyncio
async def test_search_request():
    """Test basic search functionality."""
    client = MCPZenodoClient()
    request = MCPRequest(
        query="test query",
        max_results=5
    )
    
    response = await client.search(request)
    assert response is not None
    assert hasattr(response, "records")
    assert hasattr(response, "total_count")
    assert hasattr(response, "query_time") 