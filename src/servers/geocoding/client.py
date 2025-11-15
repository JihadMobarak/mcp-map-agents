"""HTTP client for Nominatim geocoding service."""

import os
import time
from math import atan2, cos, radians, sin, sqrt
from typing import Any

import httpx

from src.agents.schemas import ToolResponse, ToolUsage

# Overpass API endpoint for POI searches
OVERPASS_API = "https://overpass-api.de/api/interpreter"


class NominatimClient:
    """Client for OpenStreetMap Nominatim geocoding service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        """Initialize the Nominatim client.

        Args:
            base_url: Base URL for Nominatim API (default from env or public)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
        )
        self.timeout = timeout or float(
            os.getenv("NOMINATIM_TIMEOUT_SECONDS", "10")
        )
        self.user_agent = "mcp-map-agents/0.1"

    async def forward_geocode(
        self, query: str, limit: int = 5
    ) -> ToolResponse:
        """Geocode an address string to coordinates.

        Args:
            query: Address or place name to geocode
            limit: Maximum number of results

        Returns:
            ToolResponse with geocoding results
        """
        start_time = time.time()
        endpoint = f"{self.base_url}/search"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params={
                        "q": query,
                        "format": "json",
                        "limit": limit,
                    },
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

            results = response.json()
            duration_ms = (time.time() - start_time) * 1000

            if not results:
                return ToolResponse(
                    status="success",
                    data={"results": [], "query": query},
                    message="No results found",
                    usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
                )

            formatted_results = [
                {
                    "name": r.get("display_name", ""),
                    "latitude": float(r.get("lat", 0)),
                    "longitude": float(r.get("lon", 0)),
                    "importance": r.get("importance", 0),
                }
                for r in results
            ]

            return ToolResponse(
                status="success",
                data={"results": formatted_results, "query": query},
                message=f"Found {len(results)} result(s)",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message="Nominatim request timed out",
                error_code="TIMEOUT",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message=f"Nominatim API error: {str(e)}",
                error_code="HTTP_ERROR",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> ToolResponse:
        """Reverse geocode coordinates to an address.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            ToolResponse with address information
        """
        start_time = time.time()
        endpoint = f"{self.base_url}/reverse"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "json",
                    },
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()

            result = response.json()
            duration_ms = (time.time() - start_time) * 1000

            return ToolResponse(
                status="success",
                data={
                    "address": result.get("address", {}),
                    "display_name": result.get("display_name", ""),
                    "latitude": latitude,
                    "longitude": longitude,
                },
                message="Reverse geocoding successful",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message="Nominatim request timed out",
                error_code="TIMEOUT",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResponse(
                status="error",
                message=f"Nominatim API error: {str(e)}",
                error_code="HTTP_ERROR",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

    async def poi_search(self, query: str, latitude: float, longitude: float, radius: float = 1000) -> ToolResponse:
        """Search for POIs near a location using Overpass API with fallback.

        Uses Overpass API for reliable amenity-based searches with fallback to
        wider radius if no results found.

        Args:
            query: POI type/name to search for (e.g., "restaurant", "museum", "cafe")
            latitude: Latitude of center point
            longitude: Longitude of center point
            radius: Search radius in meters

        Returns:
            ToolResponse with POI search results
        """
        start_time = time.time()

        # Amenity mapping for Overpass queries
        amenity_map = {
            "restaurant": "amenity=restaurant",
            "cafe": "amenity=cafe",
            "coffee": "amenity=cafe",
            "bar": "amenity=bar",
            "pub": "amenity=pub",
            "museum": "tourism=museum",
            "hotel": "tourism=hotel",
            "hospital": "amenity=hospital",
            "pharmacy": "amenity=pharmacy",
            "park": "leisure=park",
            "school": "amenity=school",
            "shop": "shop=*",
            "grocery": "shop=supermarket|shop=convenience",
            "church": "amenity=place_of_worship",
            "mosque": 'amenity=place_of_worship;religion=muslim',
        }

        # Detect amenity type from query
        query_lower = query.lower().strip()
        amenity_tag = None
        for key, tag in amenity_map.items():
            if key in query_lower:
                amenity_tag = tag
                break

        if not amenity_tag:
            # Fall back to name search if no amenity match
            amenity_tag = f'name~"{query}",i'

        # Try progressively larger radii if needed
        search_radii = [radius, radius * 1.5, radius * 3, radius * 5]
        results = []

        for search_radius in search_radii:
            results = await self._search_overpass(
                latitude, longitude, search_radius, amenity_tag, query_lower
            )
            if results:
                break

        duration_ms = (time.time() - start_time) * 1000
        endpoint = OVERPASS_API

        if not results:
            return ToolResponse(
                status="success",
                data={"results": [], "query": query, "center": [latitude, longitude]},
                message=f"No {query}(s) found within {int(search_radii[-1])}m radius. Try a different search term.",
                usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
            )

        # Format and sort results by distance
        formatted_results = []
        for elem in results:
            tags = elem.get("tags", {})
            lat = elem.get("lat")
            lon = elem.get("lon")

            if lat is None or lon is None:
                continue

            distance = self._haversine_distance(latitude, longitude, lat, lon)

            formatted_results.append({
                "name": tags.get("name", tags.get("brand", "Unnamed")),
                "latitude": lat,
                "longitude": lon,
                "type": tags.get("amenity") or tags.get("tourism") or tags.get("leisure") or "POI",
                "distance_meters": int(distance),
                "details": {
                    "phone": tags.get("phone"),
                    "website": tags.get("website"),
                    "opening_hours": tags.get("opening_hours"),
                } if any([tags.get("phone"), tags.get("website"), tags.get("opening_hours")]) else None,
            })

        formatted_results.sort(key=lambda x: x["distance_meters"])

        return ToolResponse(
            status="success",
            data={
                "results": formatted_results[:10],  # Top 10 results
                "query": query,
                "center": [latitude, longitude],
                "search_radius_meters": int(search_radius),
                "total_found": len(formatted_results),
            },
            message=f"Found {len(formatted_results)} {query}(s) near the location (showing top 10)",
            usage=ToolUsage(endpoint=endpoint, duration_ms=duration_ms),
        )

    async def _search_overpass(
        self, latitude: float, longitude: float, radius: float, amenity_tag: str, query_lower: str
    ) -> list[dict[str, Any]]:
        """Search Overpass API for POIs with fallback to Nominatim.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters
            amenity_tag: OSM amenity tag (e.g., "amenity=restaurant")
            query_lower: Lowercase query for fallback search

        Returns:
            List of OSM elements or empty list
        """
        try:
            # Try Overpass API first
            bbox_query = f"(around:{int(radius)},{latitude},{longitude})"
            filter_query = f"node{bbox_query}[{amenity_tag}];way{bbox_query}[{amenity_tag}];relation{bbox_query}[{amenity_tag}];"

            overpass_query = f"""
            [out:json];
            (
              {filter_query}
            );
            out body;
            """

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    OVERPASS_API,
                    content=overpass_query,
                    headers={"User-Agent": self.user_agent},
                    timeout=15.0,
                )
                response.raise_for_status()

            data: dict[str, Any] = response.json()
            result = data.get("elements", [])
            return result if isinstance(result, list) else []

        except (httpx.TimeoutException, httpx.HTTPError):
            # Silently fail to allow fallback to larger radius
            return []

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in meters using Haversine formula.

        Args:
            lat1, lon1: Starting coordinates
            lat2, lon2: Ending coordinates

        Returns:
            Distance in meters
        """
        earth_radius_m = 6371000  # Earth's radius in meters
        phi1, phi2 = radians(lat1), radians(lat2)
        delta_phi = radians(lat2 - lat1)
        delta_lambda = radians(lon2 - lon1)

        a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earth_radius_m * c
