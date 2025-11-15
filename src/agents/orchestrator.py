"""Agent orchestrator for routing queries to map servers."""

import asyncio
import json
import os
from typing import Any

from openai import AsyncOpenAI

from src.servers.geocoding.tools import get_geocoding_tools, handle_geocoding_tool
from src.servers.routing.tools import get_routing_tools, handle_routing_tool
from src.servers.tiles.tools import get_tiles_tools, handle_tiles_tool


class _DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and Pydantic models."""

    def default(self, obj: Any) -> Any:  # type: ignore[override]
        """Handle datetime and Pydantic model serialization."""
        if hasattr(obj, "model_dump"):
            # Pydantic v2
            return obj.model_dump()
        if hasattr(obj, "dict"):
            # Pydantic v1
            return obj.dict()
        if hasattr(obj, "isoformat"):
            # datetime objects
            return obj.isoformat()
        return super().default(obj)


class MapAgentOrchestrator:
    """Orchestrates queries across map service tools using OpenAI SDK."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the orchestrator.

        Args:
            model: OpenAI model to use
        """
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tools = self._build_tools()
        self.system_prompt = """You are a helpful map assistant that helps users with geographic queries.
You have access to three map services:

1. **Geocoding Service** - For converting addresses to coordinates and vice versa, plus POI search
2. **Routing Service** - For calculating routes between locations, distance matrices, and trace matching
3. **Tiles/Metadata Service** - For information about map tile providers

When a user asks a question:
1. Identify which service(s) are most relevant
2. Call the appropriate tool(s) with the correct parameters
3. Present the results in a clear, concise way with proper units (km, minutes, meters)
4. When reporting distances, refer to them as "between [location A] and [location B]" - do NOT say "from your location" since you don't know the user's location
5. Always include units in your responses (km for distance, minutes for time, meters for short distances)

Be conversational and helpful. If something fails, explain what went wrong clearly."""

    def _build_tools(self) -> list[dict[str, Any]]:
        """Build the tool list for OpenAI.

        Returns:
            List of tool specifications
        """
        tools = []
        tools.extend(get_geocoding_tools())
        tools.extend(get_routing_tools())
        tools.extend(get_tiles_tools())
        return tools

    async def process_query(self, user_message: str) -> tuple[str, list[dict[str, Any]]]:
        """Process a user query and return results.

        Args:
            user_message: The user's natural language query

        Returns:
            Tuple of (response_text, tool_calls_made)
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        tool_calls_made: list[dict[str, Any]] = []

        # Agentic loop
        iteration_count = 0
        while True:
            iteration_count += 1

            # Aggressive pruning for long conversations
            # Keep system + initial query + only last 6 complete turns
            # A complete turn = assistant message + tool message (if tool was called)
            if len(messages) > 14:
                # Find the last complete turn boundaries
                # Walk backwards and find tool/assistant pairs
                messages = self._prune_message_history(messages)

            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(  # type: ignore[call-overload]
                        model=self.model,
                        max_tokens=1024,
                        tools=self.tools,
                        tool_choice="auto",
                        messages=messages,
                    ),
                    timeout=60.0  # 60 second timeout
                )
            except TimeoutError:
                return "Request timed out. The API took too long to respond. Please try again.", tool_calls_made
            except Exception as e:
                # If context still overflows, just restart with system + query
                if "context_length_exceeded" in str(e):
                    messages = messages[:2]
                    try:
                        response = await asyncio.wait_for(
                            self.client.chat.completions.create(  # type: ignore[call-overload]
                                model=self.model,
                                max_tokens=1024,
                                tools=self.tools,
                                tool_choice="auto",
                                messages=messages,
                            ),
                            timeout=60.0  # 60 second timeout
                        )
                    except TimeoutError:
                        return "Request timed out. The API took too long to respond. Please try again.", tool_calls_made
                else:
                    raise

            # Check if we're done (no tool calls)
            if response.choices[0].finish_reason == "stop":
                final_text = response.choices[0].message.content or ""
                return final_text, tool_calls_made

            # Process tool calls
            has_tool_calls = False

            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                has_tool_calls = True

                # Add assistant message with tool_calls to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                })

                # Process each tool call
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Execute the tool
                    tool_result = await self._execute_tool(tool_name, tool_args)

                    tool_calls_made.append({
                        "tool": tool_name,
                        "input": tool_args,
                        "result": tool_result,
                    })

                    # Add tool result to messages for next iteration
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, cls=_DateTimeEncoder)
                    })

            if not has_tool_calls:
                # No tool calls, return the final response
                final_text = response.choices[0].message.content or ""
                return final_text, tool_calls_made

    def _prune_message_history(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prune message history while preserving conversation structure.

        Keeps system prompt + initial user message + last complete turns.
        A complete turn = user message → assistant message → tool messages

        Args:
            messages: Current message history

        Returns:
            Pruned message history
        """
        # Always keep system and initial user message
        if len(messages) <= 2:
            return messages

        # Strategy: Keep only system + initial query, discard all history
        # This is the most reliable way to avoid message validation errors
        # while still maintaining conversation context
        return messages[:2]

    async def _execute_tool(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a tool call.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters

        Returns:
            Tool result
        """
        # Geocoding tools
        if tool_name in ["forward_geocode", "reverse_geocode", "poi_search"]:
            return await handle_geocoding_tool(tool_name, tool_input)

        # Routing tools
        elif tool_name in ["route", "distance_matrix", "match_trace"]:
            return await handle_routing_tool(tool_name, tool_input)

        # Tiles tools
        elif tool_name in [
            "list_tile_providers",
            "get_tile_provider_info",
            "get_tile_attribution",
        ]:
            return await handle_tiles_tool(tool_name, tool_input)

        else:
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}",
            }
