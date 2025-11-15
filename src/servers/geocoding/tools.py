"""Tool definitions for the Geocoding server."""

from typing import Any

from src.servers.geocoding.client import NominatimClient


def get_geocoding_tools() -> list[dict[str, Any]]:
    """Get tool specifications for geocoding server.

    Returns:
        List of tool specification dictionaries for OpenAI SDK.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "forward_geocode",
                "description": "Convert an address or place name to geographic coordinates (latitude/longitude)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The address or place name to geocode (e.g., 'New York City', '1600 Pennsylvania Avenue')",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "reverse_geocode",
                "description": "Convert geographic coordinates (latitude/longitude) to an address",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude in decimal degrees (e.g., 40.7128)",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude in decimal degrees (e.g., -74.0060)",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "poi_search",
                "description": "Search for points of interest (restaurants, hotels, landmarks, etc.) near a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The type of POI to search for (e.g., 'restaurants', 'hotels', 'museums')",
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Latitude of the center point",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude of the center point",
                        },
                        "radius": {
                            "type": "number",
                            "description": "Search radius in meters (default: 1000)",
                            "default": 1000,
                        },
                    },
                    "required": ["query", "latitude", "longitude"],
                },
            },
        },
    ]


def get_geocoding_server_info() -> dict[str, Any]:
    """Get metadata about the geocoding server.

    Returns:
        Dictionary with server information.
    """
    return {
        "name": "Geocoding Server",
        "description": "OpenStreetMap Nominatim-based geocoding service for forward/reverse geocoding and POI search",
        "tools": get_geocoding_tools(),
        "base_url": "https://nominatim.openstreetmap.org",
    }


async def handle_geocoding_tool(
    tool_name: str, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Handle geocoding tool invocations.

    Args:
        tool_name: Name of the tool to invoke
        tool_input: Input parameters for the tool

    Returns:
        Tool response as dictionary
    """
    client = NominatimClient()

    if tool_name == "forward_geocode":
        result = await client.forward_geocode(
            query=tool_input.get("query", ""),
            limit=tool_input.get("limit", 5),
        )
    elif tool_name == "reverse_geocode":
        result = await client.reverse_geocode(
            latitude=tool_input.get("latitude", 0),
            longitude=tool_input.get("longitude", 0),
        )
    elif tool_name == "poi_search":
        result = await client.poi_search(
            query=tool_input.get("query", ""),
            latitude=tool_input.get("latitude", 0),
            longitude=tool_input.get("longitude", 0),
            radius=tool_input.get("radius", 1000),
        )
    else:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    return result.model_dump(exclude_none=True)
