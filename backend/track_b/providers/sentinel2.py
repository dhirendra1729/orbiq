"""Sentinel-2 multispectral optical discovery and cloud quality assessment."""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import shape, box

from track_b.config import settings
from track_b.schemas import SceneMetadata
from track_b.providers.stac import search_stac_items


def discover_sentinel2_scenes(
    aoi_geometry: Dict[str, Any],
    event_date_str: str,
    max_cloud_cover_percent: float = 60.0,
    search_days_pre: int = 30,
    search_days_post: int = 20
) -> Tuple[List[SceneMetadata], List[SceneMetadata]]:
    """Discover clear Sentinel-2 L2A optical scenes before and after the event.

    Returns:
        (pre_event_scenes, post_event_scenes)
    """
    event_d = date.fromisoformat(event_date_str)
    event_dt = datetime.combine(event_d, datetime.min.time(), tzinfo=timezone.utc)

    start_str = (event_dt - timedelta(days=search_days_pre)).strftime("%Y-%m-%dT00:00:00Z")
    end_str = (event_dt + timedelta(days=search_days_post)).strftime("%Y-%m-%dT23:59:59Z")

    raw_items = search_stac_items(
        collections=["sentinel-2-l2a"],
        aoi_geometry=aoi_geometry,
        start_date_utc=start_str,
        end_date_utc=end_str,
        catalog_url=settings.earth_search_stac_url
    )

    pre_scenes: List[SceneMetadata] = []
    post_scenes: List[SceneMetadata] = []

    for item in raw_items:
        props = item.get("properties", {})
        cloud_cover = float(props.get("eo:cloud_cover", 100.0))
        if cloud_cover > max_cloud_cover_percent:
            continue

        dt_str = props.get("datetime", "")
        if not dt_str:
            continue

        try:
            clean_dt = dt_str.replace("Z", "+00:00")
            sc_dt = datetime.fromisoformat(clean_dt)
        except Exception:
            continue

        raw_assets = item.get("assets", {})
        asset_urls = {k: v.get("href") for k, v in raw_assets.items() if isinstance(v, dict) and "href" in v}

        scene_meta = SceneMetadata(
            product_id=item.get("id", ""),
            collection="sentinel-2-l2a",
            acquisition_utc=dt_str,
            platform=props.get("platform", "sentinel-2"),
            relative_orbit=None,
            orbit_direction="descending",
            instrument_mode="MSI",
            polarizations=[],
            processing_level="L2A",
            bounding_box=item.get("bbox", [0.0, 0.0, 0.0, 0.0]),
            coverage_fraction=1.0 - (cloud_cover / 100.0),
            asset_urls=asset_urls,
            scene_valid=True
        )

        if sc_dt < event_dt:
            pre_scenes.append(scene_meta)
        else:
            post_scenes.append(scene_meta)

    # Sort pre scenes by closest to event (descending datetime)
    pre_scenes.sort(key=lambda s: s.acquisition_utc, reverse=True)
    # Sort post scenes by earliest post-event (ascending datetime)
    post_scenes.sort(key=lambda s: s.acquisition_utc)

    return pre_scenes, post_scenes
