"""Tool definitions for the Tiles/Metadata server."""

from typing import Any

from src.agents.schemas import ToolResponse
from src.servers.tiles.providers import (
    get_attribution,
    get_provider_info,
    get_tile_providers,
    list_providers,
)


def get_tiles_tools() -> list[dict[str, Any]]:
    """Get tool specifications for tiles server.

    Returns:
        List of tool specification dictionaries for OpenAI SDK.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "list_tile_providers",
                "description": "List all available tile layer providers with basic information",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_tile_provider_info",
                "description": "Get detailed information about a specific tile provider including URL template and attribution",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider_id": {
                            "type": "string",
                            "description": "The ID of the tile provider (e.g., 'openstreetmap', 'carto_positron')",
                        },
                    },
                    "required": ["provider_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_tile_attribution",
                "description": "Get the attribution/credit string for a specific tile provider",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider_id": {
                            "type": "string",
                            "description": "The ID of the tile provider",
                        },
                    },
                    "required": ["provider_id"],
                },
            },
        },
    ]


def get_tiles_server_info() -> dict[str, Any]:
    """Get metadata about the tiles server.

    Returns:
        Dictionary with server information.
    """
    return {
        "name": "Tiles/Metadata Server",
        "description": "Map tile provider metadata service with provider list, URL templates, and attributions",
        "tools": get_tiles_tools(),
        "resources": list_providers(),
    }


async def handle_tiles_tool(
    tool_name: str, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Handle tiles tool invocations.

    Args:
        tool_name: Name of the tool to invoke
        tool_input: Input parameters for the tool

    Returns:
        Tool response as dictionary
    """
    if tool_name == "list_tile_providers":
        providers = get_tile_providers()
        provider_list = [
            {
                "id": provider_id,
                "name": info["name"],
                "description": info["description"],
            }
            for provider_id, info in providers.items()
        ]
        result = ToolResponse(
            status="success",
            data={"providers": provider_list, "count": len(provider_list)},
            message=f"Found {len(provider_list)} tile providers",
        )

    elif tool_name == "get_tile_provider_info":
        provider_id = tool_input.get("provider_id", "")
        info = get_provider_info(provider_id)

        if not info:
            result = ToolResponse(
                status="error",
                message=f"Provider '{provider_id}' not found",
                error_code="NOT_FOUND",
            )
        else:
            result = ToolResponse(
                status="success",
                data=info,
                message=f"Provider information for {provider_id}",
            )

    elif tool_name == "get_tile_attribution":
        provider_id = tool_input.get("provider_id", "")
        attribution = get_attribution(provider_id)

        if attribution is None:
            result = ToolResponse(
                status="error",
                message=f"Provider '{provider_id}' not found",
                error_code="NOT_FOUND",
            )
        else:
            result = ToolResponse(
                status="success",
                data={"provider_id": provider_id, "attribution": attribution},
                message=f"Attribution for {provider_id}",
            )

    else:
        result = ToolResponse(
            status="error",
            message=f"Unknown tool: {tool_name}",
            error_code="UNKNOWN_TOOL",
        )

    return result.model_dump(exclude_none=True)
