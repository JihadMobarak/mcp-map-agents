"""Tile provider metadata service."""

from typing import Any

# Tile provider definitions
TILE_PROVIDERS = {
    "openstreetmap": {
        "name": "OpenStreetMap",
        "description": "The Free and Open Collaborative Mapping Project",
        "url_template": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "min_zoom": 0,
        "max_zoom": 19,
        "attribution": "&copy; OpenStreetMap contributors",
        "license": "ODbL",
    },
    "stamen_toner": {
        "name": "Stamen Toner",
        "description": "Minimalist map tiles",
        "url_template": "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png",
        "min_zoom": 0,
        "max_zoom": 20,
        "attribution": "Map tiles by Stadia Maps, Data by OpenStreetMap",
        "license": "CC BY 3.0",
    },
    "stamen_tonerbackground": {
        "name": "Stamen Toner Background",
        "description": "Toner map without labels",
        "url_template": "https://tiles.stadiamaps.com/tiles/stamen_toner_background/{z}/{x}/{y}.png",
        "min_zoom": 0,
        "max_zoom": 20,
        "attribution": "Map tiles by Stadia Maps, Data by OpenStreetMap",
        "license": "CC BY 3.0",
    },
    "carto_positron": {
        "name": "CARTO Positron",
        "description": "Light basemap with detailed labels",
        "url_template": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "min_zoom": 0,
        "max_zoom": 19,
        "attribution": "&copy; OpenStreetMap contributors &copy; CARTO",
        "license": "CC BY 4.0",
    },
    "carto_voyager": {
        "name": "CARTO Voyager",
        "description": "Colorful and detailed basemap",
        "url_template": "https://cartodb-basemaps-a.global.ssl.fastly.net/rastered_and_labels/{z}/{x}/{y}.png",
        "min_zoom": 0,
        "max_zoom": 19,
        "attribution": "&copy; OpenStreetMap contributors &copy; CARTO",
        "license": "CC BY 4.0",
    },
    "usgs_topo": {
        "name": "USGS Topo",
        "description": "USGS topographic maps",
        "url_template": "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",
        "min_zoom": 0,
        "max_zoom": 16,
        "attribution": "USGS",
        "license": "Public Domain",
    },
}


def get_tile_providers() -> dict[str, Any]:
    """Get all available tile providers.

    Returns:
        Dictionary of tile providers
    """
    return TILE_PROVIDERS


def get_tile_provider(provider_id: str) -> dict[str, Any] | None:
    """Get a specific tile provider by ID.

    Args:
        provider_id: The ID of the provider

    Returns:
        Provider information or None if not found
    """
    return TILE_PROVIDERS.get(provider_id)


def list_providers() -> list[str]:
    """List all available provider IDs.

    Returns:
        List of provider IDs
    """
    return list(TILE_PROVIDERS.keys())


def get_provider_info(provider_id: str) -> dict[str, Any] | None:
    """Get detailed information about a provider.

    Args:
        provider_id: The ID of the provider

    Returns:
        Detailed provider information
    """
    provider = get_tile_provider(provider_id)
    if provider:
        return {
            **provider,
            "id": provider_id,
        }
    return None


def get_attribution(provider_id: str) -> str | None:
    """Get the attribution string for a provider.

    Args:
        provider_id: The ID of the provider

    Returns:
        Attribution string or None
    """
    provider = get_tile_provider(provider_id)
    return provider.get("attribution") if provider else None
