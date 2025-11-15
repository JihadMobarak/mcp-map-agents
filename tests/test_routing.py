"""Tests for the Routing server."""

import pytest

from src.agents.schemas import ToolResponse
from src.servers.routing.client import OSRMClient
from src.servers.routing.tools import (
    get_routing_server_info,
    get_routing_tools,
    handle_routing_tool,
)


def test_routing_tools_available() -> None:
    """Test that routing tools are defined."""
    tools = get_routing_tools()
    assert len(tools) == 3
    tool_names = [t["function"]["name"] for t in tools]
    assert "route" in tool_names
    assert "distance_matrix" in tool_names
    assert "match_trace" in tool_names


def test_routing_server_info() -> None:
    """Test that server info is properly defined."""
    info = get_routing_server_info()
    assert info["name"] == "Routing Server"
    assert "description" in info
    assert len(info["tools"]) == 3
    assert info["base_url"] == "http://router.project-osrm.org"


def test_route_tool_schema() -> None:
    """Test route tool has correct schema."""
    tools = get_routing_tools()
    route_tool = next(t for t in tools if t["function"]["name"] == "route")

    assert "parameters" in route_tool["function"]
    params = route_tool["function"]["parameters"]
    required = set(params["required"])
    assert "start_latitude" in required
    assert "start_longitude" in required
    assert "end_latitude" in required
    assert "end_longitude" in required


def test_distance_matrix_tool_schema() -> None:
    """Test distance matrix tool has correct schema."""
    tools = get_routing_tools()
    matrix_tool = next(t for t in tools if t["function"]["name"] == "distance_matrix")

    assert "parameters" in matrix_tool["function"]
    params = matrix_tool["function"]["parameters"]
    assert "sources" in params["required"]
    assert "destinations" in params["required"]


def test_match_trace_tool_schema() -> None:
    """Test match trace tool has correct schema."""
    tools = get_routing_tools()
    match_tool = next(t for t in tools if t["function"]["name"] == "match_trace")

    assert "parameters" in match_tool["function"]
    params = match_tool["function"]["parameters"]
    assert "coordinates" in params["required"]


@pytest.mark.asyncio
async def test_route_async() -> None:
    """Test route calculation (async)."""
    client = OSRMClient()
    # Test route from Times Square to Grand Central
    result = await client.route(40.7580, -73.9855, 40.7527, -73.9772, profile="car")

    assert result.status == "success"
    assert result.data is not None
    assert "distance_meters" in result.data
    assert "duration_seconds" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_distance_matrix_async() -> None:
    """Test distance matrix calculation (async)."""
    client = OSRMClient()
    sources = [(40.7128, -74.0060)]  # NYC
    destinations = [(40.7127, -74.0059), (40.7489, -73.9680)]  # Nearby points
    result = await client.distance_matrix(sources, destinations, profile="car")

    assert result.status == "success"
    assert result.data is not None
    assert "distances" in result.data
    assert "durations" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_match_trace_async() -> None:
    """Test trace matching (async)."""
    client = OSRMClient()
    # Test trace with a few points
    coordinates = [
        (40.7580, -73.9855),
        (40.7489, -73.9680),
        (40.7127, -74.0059),
    ]
    result = await client.match_trace(coordinates, profile="car")

    assert result.status == "success"
    assert result.data is not None
    assert "matchings" in result.data
    assert result.usage is not None


@pytest.mark.asyncio
async def test_distance_matrix_empty_sources() -> None:
    """Test distance matrix with empty sources."""
    client = OSRMClient()
    result = await client.distance_matrix([], [], profile="car")

    assert result.status == "error"
    assert result.error_code == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_match_trace_insufficient_points() -> None:
    """Test trace matching with insufficient points."""
    client = OSRMClient()
    result = await client.match_trace([(40.7128, -74.0060)], profile="car")

    assert result.status == "error"
    assert result.error_code == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_handle_routing_tool_unknown() -> None:
    """Test handling unknown routing tool."""
    result = await handle_routing_tool("unknown_tool", {})

    assert result["status"] == "error"
    assert "Unknown tool" in result["message"]


def test_tool_response_distance_matrix() -> None:
    """Test ToolResponse for distance matrix."""
    response = ToolResponse(
        status="success",
        data={
            "distances": [[0, 100], [100, 0]],
            "durations": [[0, 60], [60, 0]],
        },
        message="Distance matrix computed"
    )

    assert response.status == "success"
    assert response.data["distances"] == [[0, 100], [100, 0]]
    assert response.data["durations"] == [[0, 60], [60, 0]]
