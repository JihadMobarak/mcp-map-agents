"""HTTP client for OSRM routing service."""

import os
import time

import httpx

from src.agents.schemas import ToolResponse, ToolUsage


class OSRMClient:
    """Client for OpenStreetMap Routing Machine (OSRM) service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        """Initialize the OSRM client.

        Args:
            base_url: Base URL for OSRM API (default from env or public)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "OSRM_BASE_URL", "http://router.project-osrm.org"
        )
        self.timeout = timeout or float(
            os.getenv("OSRM_TIMEOUT_SECONDS", "15")
        )
        self.user_agent = "mcp-map-agents/0.1"

    async def route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        profile: str = "car",
    ) -> ToolResponse:
        """Get route between two points.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
            profile: Routing profile (car, bike, foot)

        Returns:
            ToolResponse with route information
        """
        start_time = time.time()
        endpoint = f"{self.base_url}/route/v1/{profile}/{start_lon},{start_lat};{end_lon},{end_lat}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params={
                        "overview": "full",
                        "steps": "true",
                        "geometries": "geojson",
                    },
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

            result = response.json()
            duration_ms = (time.time() - start_time) * 1000

            if not result.get("routes"):
                return ToolResponse(
                    status="error",
                    message="No route found",
                    error_code="NO_ROUTE",
                    usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
                )

            route = result["routes"][0]
            return ToolResponse(
                status="success",
                data={
                    "distance_meters": route.get("distance", 0),
                    "duration_seconds": route.get("duration", 0),
                    "geometry": route.get("geometry"),
                    "legs": route.get("legs"),
                    "profile": profile,
                },
                message=f"Route found: {route.get('distance', 0) / 1000:.1f} km, {route.get('duration', 0) / 60:.1f} minutes",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message="OSRM request timed out",
                error_code="TIMEOUT",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message=f"OSRM API error: {str(e)}",
                error_code="HTTP_ERROR",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

    async def distance_matrix(
        self,
        sources: list[tuple[float, float]],
        destinations: list[tuple[float, float]],
        profile: str = "car",
    ) -> ToolResponse:
        """Get distance/time matrix between multiple points.

        Args:
            sources: List of (latitude, longitude) tuples for sources
            destinations: List of (latitude, longitude) tuples for destinations
            profile: Routing profile (car, bike, foot)

        Returns:
            ToolResponse with distance matrix
        """
        start_time = time.time()

        if not sources or not destinations:
            return ToolResponse(
                status="error",
                message="Sources and destinations must not be empty",
                error_code="INVALID_INPUT",
            )

        # Format coordinates for OSRM (lon,lat pairs)
        coords_str = ";".join(
            [f"{lon},{lat}" for lat, lon in sources + destinations]
        )
        endpoint = f"{self.base_url}/table/v1/{profile}/{coords_str}"

        try:
            async with httpx.AsyncClient() as client:
                # Specify which indices are sources and destinations
                num_sources = len(sources)
                source_indices = ",".join(str(i) for i in range(num_sources))
                dest_indices = ",".join(
                    str(i) for i in range(num_sources, len(sources) + len(destinations))
                )

                response = await client.get(
                    endpoint,
                    params={
                        "sources": source_indices,
                        "destinations": dest_indices,
                    },
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

            result = response.json()
            duration_ms = (time.time() - start_time) * 1000

            if result.get("code") != "Ok":
                return ToolResponse(
                    status="error",
                    message=f"OSRM error: {result.get('message', 'Unknown error')}",
                    error_code="OSRM_ERROR",
                    usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
                )

            return ToolResponse(
                status="success",
                data={
                    "distances": result.get("distances"),
                    "durations": result.get("durations"),
                    "sources": result.get("sources"),
                    "destinations": result.get("destinations"),
                    "profile": profile,
                },
                message=f"Distance matrix computed for {num_sources} sources and {len(destinations)} destinations",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message="OSRM request timed out",
                error_code="TIMEOUT",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message=f"OSRM API error: {str(e)}",
                error_code="HTTP_ERROR",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

    async def match_trace(
        self, coordinates: list[tuple[float, float]], profile: str = "car"
    ) -> ToolResponse:
        """Match a trace of GPS coordinates to the road network.

        Args:
            coordinates: List of (latitude, longitude) tuples
            profile: Routing profile (car, bike, foot)

        Returns:
            ToolResponse with matched trace
        """
        start_time = time.time()

        if not coordinates or len(coordinates) < 2:
            return ToolResponse(
                status="error",
                message="Need at least 2 coordinates",
                error_code="INVALID_INPUT",
            )

        coords_str = ";".join(f"{lon},{lat}" for lat, lon in coordinates)
        endpoint = f"{self.base_url}/match/v1/{profile}/{coords_str}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                    },
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

            result = response.json()
            duration_ms = (time.time() - start_time) * 1000

            if result.get("code") != "Ok":
                return ToolResponse(
                    status="error",
                    message=f"OSRM error: {result.get('message', 'Unknown error')}",
                    error_code="OSRM_ERROR",
                    usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
                )

            return ToolResponse(
                status="success",
                data={
                    "matchings": result.get("matchings"),
                    "tracepoints": result.get("tracepoints"),
                    "profile": profile,
                },
                message=f"Matched {len(result.get('matchings', []))} segment(s)",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message="OSRM request timed out",
                error_code="TIMEOUT",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message=f"OSRM API error: {str(e)}",
                error_code="HTTP_ERROR",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
