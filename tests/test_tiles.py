"""Tests for the Tiles/Metadata server."""

import pytest

from src.servers.tiles.providers import (
    get_attribution,
    get_provider_info,
    get_tile_provider,
    get_tile_providers,
    list_providers,
)
from src.servers.tiles.tools import (
    get_tiles_server_info,
    get_tiles_tools,
    handle_tiles_tool,
)


def test_tiles_tools_available() -> None:
    """Test that tiles tools are defined."""
    tools = get_tiles_tools()
    assert len(tools) == 3
    tool_names = [t["function"]["name"] for t in tools]
    assert "list_tile_providers" in tool_names
    assert "get_tile_provider_info" in tool_names
    assert "get_tile_attribution" in tool_names


def test_tiles_server_info() -> None:
    """Test that server info is properly defined."""
    info = get_tiles_server_info()
    assert info["name"] == "Tiles/Metadata Server"
    assert "description" in info
    assert len(info["tools"]) == 3
    assert "resources" in info
    assert len(info["resources"]) > 0


def test_list_tile_providers_tool_schema() -> None:
    """Test list providers tool has correct schema."""
    tools = get_tiles_tools()
    list_tool = next(
        t for t in tools if t["function"]["name"] == "list_tile_providers"
    )

    assert "parameters" in list_tool["function"]
    params = list_tool["function"]["parameters"]
    assert params["required"] == []


def test_get_tile_provider_info_tool_schema() -> None:
    """Test get provider info tool has correct schema."""
    tools = get_tiles_tools()
    info_tool = next(
        t for t in tools if t["function"]["name"] == "get_tile_provider_info"
    )

    assert "parameters" in info_tool["function"]
    params = info_tool["function"]["parameters"]
    assert "provider_id" in params["properties"]
    assert "provider_id" in params["required"]


def test_get_attribution_tool_schema() -> None:
    """Test get attribution tool has correct schema."""
    tools = get_tiles_tools()
    attr_tool = next(
        t for t in tools if t["function"]["name"] == "get_tile_attribution"
    )

    assert "parameters" in attr_tool["function"]
    params = attr_tool["function"]["parameters"]
    assert "provider_id" in params["properties"]
    assert "provider_id" in params["required"]


def test_tile_providers_exist() -> None:
    """Test that tile providers are defined."""
    providers = get_tile_providers()
    assert len(providers) > 0
    assert "openstreetmap" in providers


def test_get_openstreetmap_provider() -> None:
    """Test getting OpenStreetMap provider."""
    provider = get_tile_provider("openstreetmap")
    assert provider is not None
    assert "name" in provider
    assert "url_template" in provider
    assert "attribution" in provider


def test_get_nonexistent_provider() -> None:
    """Test getting nonexistent provider."""
    provider = get_tile_provider("nonexistent_provider")
    assert provider is None


def test_list_provider_ids() -> None:
    """Test listing provider IDs."""
    provider_ids = list_providers()
    assert len(provider_ids) > 0
    assert "openstreetmap" in provider_ids
    assert all(isinstance(pid, str) for pid in provider_ids)


def test_get_provider_info_with_id() -> None:
    """Test getting detailed provider info."""
    info = get_provider_info("openstreetmap")
    assert info is not None
    assert info["id"] == "openstreetmap"
    assert "name" in info
    assert "description" in info
    assert "url_template" in info


def test_get_attribution_string() -> None:
    """Test getting attribution string."""
    attribution = get_attribution("openstreetmap")
    assert attribution is not None
    assert isinstance(attribution, str)
    assert len(attribution) > 0


def test_get_attribution_nonexistent() -> None:
    """Test getting attribution for nonexistent provider."""
    attribution = get_attribution("nonexistent_provider")
    assert attribution is None


@pytest.mark.asyncio
async def test_handle_list_providers() -> None:
    """Test handling list providers tool."""
    result = await handle_tiles_tool("list_tile_providers", {})

    assert result["status"] == "success"
    assert "providers" in result["data"]
    assert len(result["data"]["providers"]) > 0


@pytest.mark.asyncio
async def test_handle_get_provider_info() -> None:
    """Test handling get provider info tool."""
    result = await handle_tiles_tool(
        "get_tile_provider_info",
        {"provider_id": "openstreetmap"}
    )

    assert result["status"] == "success"
    assert "name" in result["data"]
    assert result["data"]["id"] == "openstreetmap"


@pytest.mark.asyncio
async def test_handle_get_provider_info_not_found() -> None:
    """Test handling get provider info with nonexistent provider."""
    result = await handle_tiles_tool(
        "get_tile_provider_info",
        {"provider_id": "nonexistent"}
    )

    assert result["status"] == "error"
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_handle_get_attribution() -> None:
    """Test handling get attribution tool."""
    result = await handle_tiles_tool(
        "get_tile_attribution",
        {"provider_id": "openstreetmap"}
    )

    assert result["status"] == "success"
    assert "attribution" in result["data"]


@pytest.mark.asyncio
async def test_handle_get_attribution_not_found() -> None:
    """Test handling get attribution with nonexistent provider."""
    result = await handle_tiles_tool(
        "get_tile_attribution",
        {"provider_id": "nonexistent"}
    )

    assert result["status"] == "error"
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_handle_tiles_tool_unknown() -> None:
    """Test handling unknown tiles tool."""
    result = await handle_tiles_tool("unknown_tool", {})

    assert result["status"] == "error"
    assert result["error_code"] == "UNKNOWN_TOOL"


def test_provider_has_required_fields() -> None:
    """Test that all providers have required fields."""
    providers = get_tile_providers()

    for provider_id, provider in providers.items():
        assert "name" in provider
        assert "description" in provider
        assert "url_template" in provider
        assert "attribution" in provider
        assert "license" in provider
