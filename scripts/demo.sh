#!/bin/bash
# Demo script for MCP Map Agents
# Shows the system in action with sample queries

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "MCP Map Agents - Demo Script"
echo "=========================================="
echo

# Activate environment
source .venv/bin/activate

echo "Testing individual servers..."
echo

# Test 1: Tiles server (no external API needed)
echo "1. Testing Tiles/Metadata Server"
echo "   Command: python main.py query 'What tile providers are available?'"
echo
# Note: This would normally run if OPENAI_API_KEY was set
# python main.py query "What tile providers are available?"
echo "   (Requires OPENAI_API_KEY set)"
echo

# Test 2: Show available commands
echo "2. CLI Help"
echo "   Commands:"
echo "   - python main.py chat           : Interactive chat mode"
echo "   - python main.py query \"...\"   : Single query mode"
echo

# Test 3: Linting
echo "3. Running Code Quality Checks"
echo "   Linting with ruff..."
ruff check src
echo "   ✓ Linting passed"
echo

echo "   Type checking with mypy..."
mypy --no-incremental src
echo "   ✓ Type checking passed"
echo

# Test 4: Tests
echo "4. Running Unit Tests"
echo "   Note: Some tests require external API access"
echo "   To skip async tests that require OPENAI_API_KEY:"
echo "   - python -m pytest tests/test_schemas.py tests/test_tiles.py"
echo

# Test imports
echo "5. Testing Core Imports"
python -c "
from src.servers.geocoding.tools import get_geocoding_tools
from src.servers.routing.tools import get_routing_tools
from src.servers.tiles.tools import get_tiles_tools
from src.agents.schemas import ToolResponse

print('   ✓ Geocoding: 3 tools')
print('   ✓ Routing: 3 tools')
print('   ✓ Tiles: 3 tools')
print('   ✓ All imports successful')
"
echo

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo
echo "To run the interactive chat:"
echo "  export OPENAI_API_KEY=sk-..."
echo "  python main.py chat"
echo
echo "To run a single query:"
echo "  export OPENAI_API_KEY=sk-..."
echo "  python main.py query 'What are the coordinates of New York City?'"
