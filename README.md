# MCP Map Agents

A Python application demonstrating the Model Context Protocol (MCP) pattern by exposing multiple map servers (Geocoding, Routing, Tiles) as agent tools using OpenAI's Agents SDK.

This project implements an intelligent, conversational map query assistant that understands natural language questions about geographic data and dynamically routes them to the appropriate services. It demonstrates advanced patterns in AI-driven system design including agentic loops, multi-tool orchestration, and context management.

## Overview

This project creates an intelligent geographic assistant that:

- **Understands Intent**: Processes natural language questions about locations, routes, and maps
- **Routes Intelligently**: Uses OpenAI's Agents SDK to decide which tool(s) to invoke
- **Integrates Multiple Services**: Seamlessly combines three independent map services:
  - **Geocoding Server**: Address ↔ Coordinates conversion, POI search (OpenStreetMap Nominatim)
  - **Routing Server**: Route planning, distance matrices, GPS trace matching (OSRM)
  - **Tiles/Metadata Server**: Map tile provider information and attribution
- **Provides Rich Responses**: Returns structured geographic data with performance metrics

The system uses OpenAI's function-calling API to autonomously select and invoke the right tools for each query, making it fully conversational and context-aware.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Typer CLI / Interactive Chat               │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│    MapAgentOrchestrator (OpenAI Agents SDK)        │
│  - Agentic loop with tool calling                  │
│  - Intent routing via LLM                           │
└─────────────────────────────────────────────────────┘
        ↓              ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Geocoding   │  │  Routing     │  │  Tiles       │
│  Server      │  │  Server      │  │  Server      │
└──────────────┘  └──────────────┘  └──────────────┘
        ↓              ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Nominatim    │  │ OSRM         │  │ Static Data  │
│ (HTTP)       │  │ (HTTP)       │  │ (In-memory)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Features

### Tools Available

#### Geocoding (Forward/Reverse/POI Search)
```bash
$ python main.py query "What are the coordinates of Times Square?"
$ python main.py query "What address is at 40.7128, -74.0060?"
$ python main.py query "Find restaurants near Central Park"
```

#### Routing
```bash
$ python main.py query "Route from NYC to Boston by car"
$ python main.py query "Distance matrix between these 3 cities"
$ python main.py query "Match this GPS trace to roads"
```

#### Tile Providers
```bash
$ python main.py query "List available map tile providers"
$ python main.py query "Tell me about OpenStreetMap tiles"
$ python main.py query "Attribution for CARTO Positron?"
```

### Quality Assurance

- **Unit Tests**: Comprehensive pytest suite covering 3 servers and 9+ tools
- **Type Safety**: mypy strict mode for all code
- **Linting**: Ruff enforcing code quality
- **Coverage**: Aim for 60%+ across all modules

## Setup

### Requirements
- Python 3.11+
- OpenAI API key (set `OPENAI_API_KEY` env var)
- Internet access to Nominatim and OSRM public endpoints

### Installation

```bash
# Clone and navigate to project
cd mcp-map-agents

# Create virtual environment (using Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file (optional, defaults work for public APIs):
```env
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
NOMINATIM_TIMEOUT_SECONDS=10
OSRM_BASE_URL=http://router.project-osrm.org
OSRM_TIMEOUT_SECONDS=15
OPENAI_API_KEY=sk-your-key-here
```

## Usage

### Interactive Mode
```bash
python main.py chat
# Then ask questions naturally:
# > What's the distance from NYC to Boston by car?
# > Find hotels near the Eiffel Tower
# > List all tile providers
```

### Single Query
```bash
python main.py query "What address is at 40.7128, -74.0060?"
```

### Testing
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_geocoding.py -v
```

### Code Quality
```bash
# Lint
ruff check src

# Type checking
mypy src

# All checks (lint + type + test)
make verify  # or: pytest && mypy src && ruff check src
```

## Example Queries

### Geocoding Examples
- "Geocode 'Statue of Liberty' for me"
- "What's at coordinates 48.8584, 2.2945?"
- "Find museums in Paris"

### Routing Examples
- "Calculate driving route from Boston to New York"
- "How far is San Francisco from Los Angeles?"
- "Travel time from Central Park to Times Square"

### Tiles Examples
- "Which map providers are supported?"
- "What attribution do I need for Stamen Toner?"

### Combined Examples
- "Get coordinates for the Eiffel Tower, then find nearby restaurants"
- "Route from my address [geocode it] to Central Park and show the distance"

## Project Structure

```
mcp-map-agents/
├── src/
│   ├── agents/
│   │   ├── schemas.py         # Pydantic models (ToolRequest, ToolResponse, etc.)
│   │   ├── orchestrator.py    # OpenAI Agents SDK integration & agentic loop
│   │   └── cli.py              # Typer CLI (chat, query commands)
│   └── servers/
│       ├── geocoding/
│       │   ├── client.py       # Nominatim HTTP client & geocoding logic
│       │   ├── tools.py        # Tool definitions & handlers
│       │   └── __init__.py
│       ├── routing/
│       │   ├── client.py       # OSRM HTTP client & routing logic
│       │   ├── tools.py        # Tool definitions & handlers
│       │   └── __init__.py
│       └── tiles/
│           ├── providers.py    # Tile provider metadata (6 providers)
│           ├── tools.py        # Tool definitions & handlers
│           └── __init__.py
├── tests/
│   ├── test_geocoding.py       # Geocoding server tests (8 tests)
│   ├── test_routing.py         # Routing server tests (8 tests)
│   ├── test_tiles.py           # Tiles server tests (10 tests)
│   ├── test_schemas.py         # Schema validation tests
│   └── __init__.py
├── scripts/
│   └── demo.sh                 # Quality checks & demo script
├── main.py                     # Entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata & tool configs
├── mypy.ini                    # Type checking configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Implementation Details

### Tool Registration
Each server declares tools via `get_*_tools()` returning JSON schemas compatible with OpenAI's function-calling format:
- Tool name and description
- Parameter schema (JSON Schema)
- Examples in docstrings

### Agentic Loop
The orchestrator uses OpenAI's Agents API to:
1. Accept user query
2. Let the model decide which tool(s) to call
3. Execute tools and collect results
4. Return final response with endpoint URLs and timings

### Error Handling
- HTTP timeouts → graceful error messages
- Invalid coordinates → validation before API calls
- Unknown tools → explicit error responses
- All responses include `status`, `message`, and optional `error_code`

## Testing

### Coverage
```
Geocoding: 8 tests (forward, reverse, POI, error cases, schema)
Routing:   8 tests (route, matrix, trace, error cases, schema)
Tiles:     10 tests (provider list, info, attribution, error cases)
---
Total:     ~26 tests, 65%+ code coverage
```

### Key Test Scenarios
- **Happy path**: Valid inputs return expected structured responses
- **Error cases**: Empty queries, invalid coordinates, not-found scenarios
- **Schema validation**: All tools have correct JSON schema parameters
- **Server info**: Metadata (name, description) matches expectations

## Performance

- Geocoding: ~500-1000ms per request (Nominatim public API)
- Routing: ~1000-2000ms for local routes (OSRM public API)
- Tiles: <10ms (in-memory data)
- Agent orchestration: ~2-3 seconds total (includes LLM inference time)

## Limitations & Future Work

- **Public APIs**: Uses free Nominatim and OSRM endpoints (rate limits apply)
- **MCP Protocol**: This is an MCP-style pattern, not official MCP specification
- **Future**: Could add elevation server, weather, local search, offline support
- **Performance**: Caching responses, batch requests, async pooling

## Troubleshooting

**"No route found" for OSRM:**
- Check coordinates are valid (not on islands, etc.)
- Some remote areas may not have routing coverage

**Nominatim timeouts:**
- Public API can be slow during peak hours
- Consider self-hosting for production use

**OpenAI API errors:**
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has function-calling enabled

## License

This project is provided as an educational example for EECE 503P.

## References

- [OpenStreetMap Nominatim](https://nominatim.org/)
- [OSRM (Routing Machine)](http://project-osrm.org/)
- [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents)
- [Model Context Protocol](https://modelcontextprotocol.io/) (conceptual inspiration)
- [Pydantic](https://docs.pydantic.dev/) - Data validation with Python type hints
- [Typer](https://typer.tiangolo.com/) - CLI framework for Python
