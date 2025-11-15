"""Shared schemas for tool requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Standard request format for tool invocations."""

    tool_name: str = Field(..., description="Name of the tool being invoked")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    request_id: str | None = Field(None, description="Optional request ID for tracking")


class ToolUsage(BaseModel):
    """Usage metrics for tool execution."""

    endpoint: str = Field(..., description="API endpoint used")
    duration_ms: float = Field(..., description="Duration of the request in milliseconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the request was made"
    )


class ToolResponse(BaseModel):
    """Standard response format for tool results."""

    status: str = Field(..., description="Status: 'success' or 'error'")
    data: dict[str, Any] | None = Field(default=None, description="Response data")
    message: str | None = Field(default=None, description="Human-readable message")
    usage: ToolUsage | None = Field(default=None, description="Usage metrics")
    error_code: str | None = Field(default=None, description="Error code if status is error")


class GeoPoint(BaseModel):
    """Geographic point with latitude and longitude."""

    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")

    @property
    def latlng(self) -> tuple[float, float]:
        """Return as (lat, lng) tuple."""
        return (self.latitude, self.longitude)

    @property
    def lnglat(self) -> tuple[float, float]:
        """Return as (lng, lat) tuple (for GeoJSON convention)."""
        return (self.longitude, self.latitude)


class Address(BaseModel):
    """Address information."""

    display_name: str = Field(..., description="Human-readable full address")
    house_number: str | None = None
    street: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None


class ToolSpec(BaseModel):
    """Specification for a tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(
        ..., description="JSON schema for parameters"
    )


class ServerInfo(BaseModel):
    """Information about a map server."""

    name: str = Field(..., description="Server name")
    description: str = Field(..., description="Server description")
    tools: list[ToolSpec] = Field(..., description="Available tools")
    base_url: str | None = Field(None, description="Base URL for the server")
    resources: list[str] | None = Field(None, description="Available resources")
