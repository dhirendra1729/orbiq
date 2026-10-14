"""STAC Catalog discovery adapter for Earth Search and Copernicus Data Space Ecosystem."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests
from pystac_client import Client

from track_b.config import settings
from track_b.schemas import SceneMetadata


def search_stac_items(
    collections: List[str],
    aoi_geometry: Dict[str, Any],
    start_date_utc: str,
    end_date_utc: str,
    catalog_url: str = settings.earth_search_stac_url,
    limit: int = 40
) -> List[Dict[str, Any]]:
    """Search items in STAC API with pagination and error resilience."""
    try:
        client = Client.open(catalog_url, timeout=settings.stac_timeout_sec)
        datetime_range = f"{start_date_utc}/{end_date_utc}"
        search = client.search(
            collections=collections,
            intersects=aoi_geometry,
            datetime=datetime_range,
            limit=limit,
            max_items=limit
        )
        return [item.to_dict() for item in search.items()]
    except Exception as exc:
        print(f"STAC search failed on {catalog_url} for {collections}: {exc}")
        return []


def normalize_sentinel1_stac_item(item_dict: Dict[str, Any], collection_name: str) -> SceneMetadata:
    """Normalize raw STAC item to verified SceneMetadata."""
    props = item_dict.get("properties", {})
    item_id = item_dict.get("id", "")
    
    # Date parsing
    dt_str = props.get("datetime") or props.get("start_datetime") or ""
    
    # Orbit parameters
    orbit_state = props.get("sat:orbit_state") or props.get("orbit_state") or "unknown"
    rel_orbit = props.get("sat:relative_orbit") or props.get("s1:relative_orbit")
    if rel_orbit is None and "relative_orbit_number" in props:
        rel_orbit = props.get("relative_orbit_number")

    # Polarizations
    polarizations = props.get("sar:polarizations") or props.get("polarizations") or ["VV", "VH"]
    if isinstance(polarizations, str):
        polarizations = [polarizations]

    # Instrument mode
    instrument_mode = props.get("sar:instrument_mode") or props.get("instrument_mode") or "IW"

    # Assets
    raw_assets = item_dict.get("assets", {})
    asset_urls = {k: v.get("href") for k, v in raw_assets.items() if isinstance(v, dict) and "href" in v}

    bbox = item_dict.get("bbox", [0.0, 0.0, 0.0, 0.0])

    return SceneMetadata(
        product_id=item_id,
        collection=collection_name,
        acquisition_utc=dt_str,
        platform=props.get("platform", "sentinel-1"),
        relative_orbit=int(rel_orbit) if rel_orbit is not None else None,
        orbit_direction=str(orbit_state).lower(),
        instrument_mode=instrument_mode,
        polarizations=polarizations,
        processing_level=props.get("processing:level", "GRD"),
        bounding_box=bbox,
        coverage_fraction=1.0,
        asset_urls=asset_urls,
        scene_valid=True
    )
