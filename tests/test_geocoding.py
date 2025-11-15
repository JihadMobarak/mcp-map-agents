"""Tests for the Geocoding server."""

import pytest

from src.agents.schemas import ToolResponse
from src.servers.geocoding.client import NominatimClient
from src.servers.geocoding.tools import (
    get_geocoding_server_info,
    get_geocoding_tools,
    handle_geocoding_tool,
)


def test_geocoding_tools_available() -> None:
    """Test that geocoding tools are defined."""
    tools = get_geocoding_tools()
    assert len(tools) == 3
    tool_names = [t["function"]["name"] for t in tools]
    assert "forward_geocode" in tool_names
    assert "reverse_geocode" in tool_names
    assert "poi_search" in tool_names


def test_geocoding_server_info() -> None:
    """Test that server info is properly defined."""
    info = get_geocoding_server_info()
    assert info["name"] == "Geocoding Server"
    assert "description" in info
    assert len(info["tools"]) == 3
    assert info["base_url"] == "https://nominatim.openstreetmap.org"


def test_forward_geocode_tool_schema() -> None:
    """Test forward geocode tool has correct schema."""
    tools = get_geocoding_tools()
    forward_tool = next(t for t in tools if t["function"]["name"] == "forward_geocode")

    assert "parameters" in forward_tool["function"]
    params = forward_tool["function"]["parameters"]
    assert "query" in params["properties"]
    assert "limit" in params["properties"]
    assert "query" in params["required"]


def test_reverse_geocode_tool_schema() -> None:
    """Test reverse geocode tool has correct schema."""
    tools = get_geocoding_tools()
    reverse_tool = next(t for t in tools if t["function"]["name"] == "reverse_geocode")

    assert "parameters" in reverse_tool["function"]
    params = reverse_tool["function"]["parameters"]
    assert "latitude" in params["properties"]
    assert "longitude" in params["properties"]
    assert set(params["required"]) == {"latitude", "longitude"}


def test_poi_search_tool_schema() -> None:
    """Test POI search tool has correct schema."""
    tools = get_geocoding_tools()
    poi_tool = next(t for t in tools if t["function"]["name"] == "poi_search")

    assert "parameters" in poi_tool["function"]
    params = poi_tool["function"]["parameters"]
    assert "query" in params["properties"]
    assert "latitude" in params["properties"]
    assert "longitude" in params["properties"]
    assert "query" in params["required"]


@pytest.mark.asyncio
async def test_forward_geocode_async() -> None:
    """Test forward geocoding (async)."""
    client = NominatimClient()
    result = await client.forward_geocode("New York City", limit=1)

    assert result.status == "success"
    assert result.data is not None
    assert "results" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_reverse_geocode_async() -> None:
    """Test reverse geocoding (async)."""
    client = NominatimClient()
    # Test with Times Square coordinates
    result = await client.reverse_geocode(40.7580, -73.9855)

    assert result.status == "success"
    assert result.data is not None
    assert "address" in result.data or "display_name" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_poi_search_async() -> None:
    """Test POI search (async)."""
    client = NominatimClient()
    result = await client.poi_search("restaurants", 40.7128, -74.0060, radius=1000)

    assert result.status == "success"
    assert result.data is not None
    assert "results" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_forward_geocode_empty_query() -> None:
    """Test forward geocoding with empty query."""
    client = NominatimClient()
    result = await client.forward_geocode("", limit=5)

    # Should return either success with empty results or error
    assert result.status in ["success", "error"]
    if result.status == "success":
        assert result.data is not None


@pytest.mark.asyncio
async def test_handle_geocoding_tool_unknown() -> None:
    """Test handling unknown geocoding tool."""
    result = await handle_geocoding_tool("unknown_tool", {})

    assert result["status"] == "error"
    assert "Unknown tool" in result["message"]


def test_tool_response_schema() -> None:
    """Test ToolResponse schema."""
    response = ToolResponse(
        status="success",
        data={"test": "data"},
        message="Test message"
    )

    assert response.status == "success"
    assert response.data == {"test": "data"}
    assert response.message == "Test message"
    assert response.error_code is None
