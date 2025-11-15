"""Tests for shared schemas."""

import pytest

from src.agents.schemas import (
    Address,
    GeoPoint,
    ServerInfo,
    ToolResponse,
    ToolSpec,
    ToolUsage,
)


def test_geo_point() -> None:
    """Test GeoPoint creation."""
    point = GeoPoint(latitude=40.7128, longitude=-74.0060)
    assert point.latitude == 40.7128
    assert point.longitude == -74.0060
    assert point.latlng == (40.7128, -74.0060)
    assert point.lnglat == (-74.0060, 40.7128)


def test_address() -> None:
    """Test Address creation."""
    address = Address(
        display_name="Times Square, New York",
        street="42nd Street",
        city="New York",
        country="United States",
    )
    assert address.display_name == "Times Square, New York"
    assert address.city == "New York"
    assert address.country == "United States"


def test_tool_usage() -> None:
    """Test ToolUsage creation."""
    usage = ToolUsage(endpoint="https://nominatim.openstreetmap.org/search", duration_ms=123.45)
    assert usage.endpoint == "https://nominatim.openstreetmap.org/search"
    assert usage.duration_ms == 123.45
    assert usage.timestamp is not None


def test_tool_response_success() -> None:
    """Test successful ToolResponse."""
    response = ToolResponse(
        status="success",
        data={"key": "value"},
        message="Operation successful",
    )
    assert response.status == "success"
    assert response.data == {"key": "value"}
    assert response.message == "Operation successful"
    assert response.error_code is None


def test_tool_response_error() -> None:
    """Test error ToolResponse."""
    response = ToolResponse(
        status="error",
        message="An error occurred",
        error_code="ERROR_CODE",
    )
    assert response.status == "error"
    assert response.message == "An error occurred"
    assert response.error_code == "ERROR_CODE"
    assert response.data is None


def test_tool_spec() -> None:
    """Test ToolSpec creation."""
    spec = ToolSpec(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
    )
    assert spec.name == "test_tool"
    assert spec.description == "A test tool"
    assert spec.parameters["type"] == "object"


def test_server_info() -> None:
    """Test ServerInfo creation."""
    tool1 = ToolSpec(
        name="tool1",
        description="First tool",
        parameters={"type": "object"},
    )
    tool2 = ToolSpec(
        name="tool2",
        description="Second tool",
        parameters={"type": "object"},
    )
    server = ServerInfo(
        name="Test Server",
        description="A test server",
        tools=[tool1, tool2],
        base_url="https://example.com",
        resources=["resource1", "resource2"],
    )
    assert server.name == "Test Server"
    assert len(server.tools) == 2
    assert server.base_url == "https://example.com"
    assert server.resources == ["resource1", "resource2"]


def test_tool_response_model_dump() -> None:
    """Test ToolResponse can be dumped to dict."""
    usage = ToolUsage(endpoint="https://test.com", duration_ms=100.0)
    response = ToolResponse(
        status="success",
        data={"test": "data"},
        message="Test message",
        usage=usage,
    )
    dumped = response.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["status"] == "success"
    assert dumped["data"] == {"test": "data"}


def test_tool_response_model_dump_exclude_none() -> None:
    """Test ToolResponse can exclude None values when dumping."""
    response = ToolResponse(
        status="success",
        data={"test": "data"},
    )
    dumped = response.model_dump(exclude_none=True)
    assert "message" not in dumped
    assert "error_code" not in dumped
    assert "usage" not in dumped
    assert dumped["status"] == "success"
