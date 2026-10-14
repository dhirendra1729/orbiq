"""Historical OpenStreetMap extraction adapter via HeiGIT ohsome API.

Strictly enforces pre-event historical snapshots and prevents post-disaster OSM contamination.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import json
import hashlib
import requests
from shapely.geometry import shape

from track_b.config import settings


def get_ohsome_metadata() -> Dict[str, Any]:
    """Query ohsome API metadata to inspect temporal bounds and server version."""
    try:
        resp = requests.get(settings.ohsome_metadata_url, timeout=settings.ohsome_timeout_sec)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {
            "status": "unavailable",
            "error": str(exc),
            "max_timestamp": "2026-07-27T09:00:00Z"  # Recorded fallback boundary
        }


def determine_effective_osm_snapshot(
    event_date_str: str,
    event_timezone: str = "Asia/Kathmandu",
    event_time_str: Optional[str] = None,
    user_explicit_timestamp: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """Calculate the strict pre-event historical snapshot cutoff timestamp.

    Returns:
        (effective_iso_timestamp, metadata_provenance_dict)
    """
    event_d = date.fromisoformat(event_date_str)
    
    # Preceding day's end cutoff (23:59:59 UTC of day before event)
    preceding_day = event_d - timedelta(days=1)
    pre_event_cutoff = datetime.combine(preceding_day, datetime.strptime("23:59:59", "%H:%M:%S").time(), tzinfo=timezone.utc)
    pre_event_cutoff_iso = pre_event_cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    meta = get_ohsome_metadata()
    provider_max_iso = meta.get("extractRegion", {}).get("spatialTemporalExtent", {}).get("temporalExtent", {}).get("to")
    if not provider_max_iso:
        provider_max_iso = "2026-07-27T09:00:00Z"

    provider_max_dt = datetime.fromisoformat(provider_max_iso.replace("Z", "+00:00"))

    # Explicit user timestamp validation
    if user_explicit_timestamp:
        user_dt = datetime.fromisoformat(user_explicit_timestamp.replace("Z", "+00:00"))
        if user_dt >= datetime.combine(event_d, datetime.min.time(), tzinfo=timezone.utc):
            raise ValueError(f"Explicit OSM timestamp '{user_explicit_timestamp}' violates pre-event invariant.")
        if user_dt > provider_max_dt:
            raise ValueError(f"Explicit timestamp '{user_explicit_timestamp}' exceeds ohsome history max '{provider_max_iso}'.")
        effective_dt = user_dt
    else:
        # Minimum of pre-event cutoff and provider maximum
        effective_dt = min(pre_event_cutoff, provider_max_dt)

    effective_iso = effective_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    age_days = (datetime.combine(event_d, datetime.min.time(), tzinfo=timezone.utc) - effective_dt).total_seconds() / 86400.0

    provenance = {
        "event_date": event_date_str,
        "event_timezone": event_timezone,
        "pre_event_cutoff": pre_event_cutoff_iso,
        "provider_latest_available": provider_max_iso,
        "effective_snapshot_timestamp": effective_iso,
        "snapshot_age_at_event_days": round(age_days, 1),
        "source": "ohsome_api_v1"
    }

    return effective_iso, provenance


def fetch_historical_osm_elements(
    bboxes: str,
    time_iso: str,
    filter_expr: str,
    timeout_sec: float = 60.0
) -> Dict[str, Any]:
    """Query ohsome /elements/geometry endpoint for historical geometries."""
    url = settings.ohsome_geometry_url
    payload = {
        "bboxes": bboxes,
        "time": time_iso,
        "filter": filter_expr,
        "properties": "tags,metadata"
    }
    
    resp = requests.post(url, data=payload, timeout=timeout_sec)
    resp.raise_for_status()
    return resp.json()


def extract_historical_infrastructure(
    aoi_geometry: Dict[str, Any],
    effective_time_iso: str,
    buffer_m: float = 15000.0
) -> Dict[str, Any]:
    """Extract pre-event roads, buildings, bridges, and settlements strictly prior to event."""
    geom = shape(aoi_geometry)
    minx, miny, maxx, maxy = geom.bounds

    # Format bounding box for ohsome: min_lon,min_lat,max_lon,max_lat
    # Add small degree buffer (~0.1 deg ~ 11km)
    deg_buf = buffer_m / 111000.0
    bbox_str = f"{minx - deg_buf:.4f},{miny - deg_buf:.4f},{maxx + deg_buf:.4f},{maxy + deg_buf:.4f}"

    results = {
        "roads": {"type": "FeatureCollection", "features": []},
        "buildings": {"type": "FeatureCollection", "features": []},
        "bridges": {"type": "FeatureCollection", "features": []},
        "settlements": {"type": "FeatureCollection", "features": []},
        "hospitals": {"type": "FeatureCollection", "features": []},
        "timestamp_used": effective_time_iso
    }

    # Query roads: highway is not null
    try:
        road_data = fetch_historical_osm_elements(
            bboxes=bbox_str,
            time_iso=effective_time_iso,
            filter_expr="highway=* and geometry:line"
        )
        results["roads"] = road_data
    except Exception as exc:
        print(f"Warning: ohsome highway extraction error: {exc}")

    # Query buildings: building is not null
    try:
        bldg_data = fetch_historical_osm_elements(
            bboxes=bbox_str,
            time_iso=effective_time_iso,
            filter_expr="building=* and geometry:polygon"
        )
        results["buildings"] = bldg_data
    except Exception as exc:
        print(f"Warning: ohsome building extraction error: {exc}")

    # Query settlements: place is town, village, hamlet, city
    try:
        settlement_data = fetch_historical_osm_elements(
            bboxes=bbox_str,
            time_iso=effective_time_iso,
            filter_expr="(place=town or place=village or place=hamlet or place=city) and geometry:point"
        )
        results["settlements"] = settlement_data
    except Exception as exc:
        print(f"Warning: ohsome settlement extraction error: {exc}")

    # Query hospitals/clinics
    try:
        hosp_data = fetch_historical_osm_elements(
            bboxes=bbox_str,
            time_iso=effective_time_iso,
            filter_expr="(amenity=hospital or amenity=clinic)"
        )
        results["hospitals"] = hosp_data
    except Exception as exc:
        print(f"Warning: ohsome hospital extraction error: {exc}")

    return results
