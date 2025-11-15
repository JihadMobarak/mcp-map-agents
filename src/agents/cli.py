"""CLI for the MCP Map Agents system."""

import asyncio
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.agents.orchestrator import MapAgentOrchestrator

console = Console()
app = typer.Typer(help="MCP Map Agents - Natural language map queries")


@app.command()
def chat() -> None:
    """Start an interactive chat session with the map agent."""
    console.print(
        Panel(
            "[bold cyan]MCP Map Agents[/bold cyan]\n"
            "Natural language map queries using OpenAI Agents SDK\n"
            "Type 'exit' or 'quit' to leave, '?' for help",
            expand=False,
        )
    )

    orchestrator = MapAgentOrchestrator()

    console.print(
        "\n[yellow]Welcome![/yellow] Ask me anything about:\n"
        "  • Geocoding (addresses → coordinates or vice versa)\n"
        "  • Routing (routes, travel times, distance matrices)\n"
        "  • Tile providers (map layer information)\n"
    )

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print(
                    "[yellow]Goodbye![/yellow]"
                )
                break

            if user_input == "?":
                _show_help()
                continue

            # Process the query
            console.print("[cyan]Processing...[/cyan]")
            response, tool_calls = asyncio.run(
                orchestrator.process_query(user_input)
            )

            # Display the response
            console.print("\n[bold blue]Assistant:[/bold blue]")
            console.print(Markdown(response))

            # Show tool calls if any (for debugging)
            if tool_calls:
                console.print("\n[dim]Tools used:[/dim]")
                for call in tool_calls:
                    tool_name = call["tool"]
                    if "usage" in call["result"]:
                        endpoint = call["result"]["usage"].get(
                            "endpoint", "unknown"
                        )
                        duration = call["result"]["usage"].get(
                            "duration_ms", 0
                        )
                        console.print(
                            f"  • {tool_name} ({endpoint}) - {duration:.0f}ms"
                        )
                    else:
                        console.print(f"  • {tool_name}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if "--debug" in sys.argv:
                import traceback
                traceback.print_exc()


@app.command()
def query(message: str) -> None:
    """Execute a single query without entering interactive mode.

    Args:
        message: The query to execute
    """
    orchestrator = MapAgentOrchestrator()

    console.print(f"[bold green]Query:[/bold green] {message}")
    console.print("[cyan]Processing...[/cyan]")

    response, tool_calls = asyncio.run(orchestrator.process_query(message))

    console.print("\n[bold blue]Response:[/bold blue]")
    console.print(Markdown(response))

    if tool_calls:
        console.print("\n[dim]Tools used:[/dim]")
        for call in tool_calls:
            tool_name = call["tool"]
            if "usage" in call["result"]:
                endpoint = call["result"]["usage"].get("endpoint", "unknown")
                duration = call["result"]["usage"].get("duration_ms", 0)
                console.print(
                    f"  • {tool_name} ({endpoint}) - {duration:.0f}ms"
                )
            else:
                console.print(f"  • {tool_name}")


def _show_help() -> None:
    """Show help information."""
    help_text = """
# Available Commands

- **exit** / **quit** / **bye** - Leave the chat
- **?** - Show this help message

# Example Queries

## Geocoding
- "What are the coordinates of New York City?"
- "What address is at latitude 40.7128, longitude -74.0060?"
- "Find restaurants near Times Square"

## Routing
- "What's the driving route from Boston to New York?"
- "How long does it take to bike from Central Park to the Statue of Liberty?"
- "Calculate distances from Manhattan to Brooklyn, Queens, and the Bronx"

## Tiles
- "What tile providers are available?"
- "Tell me about the OpenStreetMap tile provider"
- "What's the attribution for the CARTO Positron tiles?"

## Combined Queries
- "Get coordinates for NYC, then find a route to Boston"
- "Geocode Central Park and find nearby museums"
"""
    console.print(Markdown(help_text))


if __name__ == "__main__":
    app()
