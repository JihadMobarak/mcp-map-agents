"""Tool definitions for the Routing server."""

from typing import Any

from src.servers.routing.client import OSRMClient


def get_routing_tools() -> list[dict[str, Any]]:
    """Get tool specifications for routing server.

    Returns:
        List of tool specification dictionaries for OpenAI SDK.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "route",
                "description": "Calculate the best route between two points",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_latitude": {
                            "type": "number",
                            "description": "Starting latitude (e.g., 40.7128)",
                        },
                        "start_longitude": {
                            "type": "number",
                            "description": "Starting longitude (e.g., -74.0060)",
                        },
                        "end_latitude": {
                            "type": "number",
                            "description": "Ending latitude",
                        },
                        "end_longitude": {
                            "type": "number",
                            "description": "Ending longitude",
                        },
                        "profile": {
                            "type": "string",
                            "description": "Routing profile: 'car', 'bike', or 'foot'",
                            "enum": ["car", "bike", "foot"],
                            "default": "car",
                        },
                    },
                    "required": [
                        "start_latitude",
                        "start_longitude",
                        "end_latitude",
                        "end_longitude",
                    ],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "distance_matrix",
                "description": "Calculate distances and travel times between multiple source and destination points",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sources": {
                            "type": "array",
                            "description": "List of [latitude, longitude] pairs for source points",
                            "items": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "number"},
                            },
                        },
                        "destinations": {
                            "type": "array",
                            "description": "List of [latitude, longitude] pairs for destination points",
                            "items": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "number"},
                            },
                        },
                        "profile": {
                            "type": "string",
                            "description": "Routing profile: 'car', 'bike', or 'foot'",
                            "enum": ["car", "bike", "foot"],
                            "default": "car",
                        },
                    },
                    "required": ["sources", "destinations"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "match_trace",
                "description": "Match a GPS trace (sequence of coordinates) to the road network",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "array",
                            "description": "List of [latitude, longitude] pairs representing the trace",
                            "items": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "number"},
                            },
                        },
                        "profile": {
                            "type": "string",
                            "description": "Routing profile: 'car', 'bike', or 'foot'",
                            "enum": ["car", "bike", "foot"],
                            "default": "car",
                        },
                    },
                    "required": ["coordinates"],
                },
            },
        },
    ]


def get_routing_server_info() -> dict[str, Any]:
    """Get metadata about the routing server.

    Returns:
        Dictionary with server information.
    """
    return {
        "name": "Routing Server",
        "description": "OpenStreetMap Routing Machine (OSRM) service for route calculation, distance matrix, and trace matching",
        "tools": get_routing_tools(),
        "base_url": "http://router.project-osrm.org",
    }


async def handle_routing_tool(
    tool_name: str, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Handle routing tool invocations.

    Args:
        tool_name: Name of the tool to invoke
        tool_input: Input parameters for the tool

    Returns:
        Tool response as dictionary
    """
    client = OSRMClient()

    if tool_name == "route":
        result = await client.route(
            start_lat=tool_input.get("start_latitude", 0),
            start_lon=tool_input.get("start_longitude", 0),
            end_lat=tool_input.get("end_latitude", 0),
            end_lon=tool_input.get("end_longitude", 0),
            profile=tool_input.get("profile", "car"),
        )
    elif tool_name == "distance_matrix":
        sources = [
            (coord[0], coord[1]) for coord in tool_input.get("sources", [])
        ]
        destinations = [
            (coord[0], coord[1]) for coord in tool_input.get("destinations", [])
        ]

        # OPTIMIZATION: For single A→B queries, use /route instead of /table
        # /table returns durations in seconds without distances
        # /route returns both distance (meters) and duration (seconds)
        if len(sources) == 1 and len(destinations) == 1:
            result = await client.route(
                start_lat=sources[0][0],
                start_lon=sources[0][1],
                end_lat=destinations[0][0],
                end_lon=destinations[0][1],
                profile=tool_input.get("profile", "car"),
            )
        else:
            result = await client.distance_matrix(
                sources=sources,
                destinations=destinations,
                profile=tool_input.get("profile", "car"),
            )
    elif tool_name == "match_trace":
        coordinates = [
            (coord[0], coord[1]) for coord in tool_input.get("coordinates", [])
        ]
        result = await client.match_trace(
            coordinates=coordinates,
            profile=tool_input.get("profile", "car"),
        )
    else:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    return result.model_dump(exclude_none=True)
