"""Sentinel-1 same-track pairing and discovery engine."""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import shape, box

from track_b.config import settings
from track_b.schemas import SceneMetadata, ScenePair
from track_b.providers.stac import search_stac_items, normalize_sentinel1_stac_item


def parse_iso_dt(dt_str: str) -> datetime:
    """Parse ISO UTC datetime string."""
    clean = dt_str.replace("Z", "+00:00")
    if "+" not in clean and "-" not in clean[10:]:
        clean += "+00:00"
    return datetime.fromisoformat(clean)


def discover_sentinel1_pairs(
    aoi_geometry: Dict[str, Any],
    event_date_str: str,
    event_time_str: Optional[str] = None,
    pre_search_days: int = 36,
    post_search_days: int = 24,
    pair_interval_days: int = 12,
    tolerance_days: int = 4
) -> Tuple[List[ScenePair], List[Dict[str, Any]]]:
    """Discover, filter, and rank same-track Sentinel-1 pre/post observation pairs.

    Returns:
        (valid_pairs, candidate_rejections)
    """
    event_d = date.fromisoformat(event_date_str)
    if event_time_str:
        event_dt = datetime.combine(event_d, datetime.strptime(event_time_str, "%H:%M:%S").time(), tzinfo=timezone.utc)
    else:
        # Default to UTC midnight of the event day
        event_dt = datetime.combine(event_d, datetime.min.time(), tzinfo=timezone.utc)

    search_start = (event_dt - timedelta(days=pre_search_days)).strftime("%Y-%m-%dT00:00:00Z")
    search_end = (event_dt + timedelta(days=post_search_days)).strftime("%Y-%m-%dT23:59:59Z")

    collections = ["sentinel-1-grd"]
    raw_items = search_stac_items(
        collections=collections,
        aoi_geometry=aoi_geometry,
        start_date_utc=search_start,
        end_date_utc=search_end,
        catalog_url=settings.earth_search_stac_url
    )

    scenes: List[SceneMetadata] = [
        normalize_sentinel1_stac_item(item, "sentinel-1-grd")
        for item in raw_items
    ]

    # Partition into pre-event (strictly before event) and post-event (at or after event)
    pre_candidates: List[SceneMetadata] = []
    post_candidates: List[SceneMetadata] = []
    rejections: List[Dict[str, Any]] = []

    aoi_shp = shape(aoi_geometry)

    for sc in scenes:
        if not sc.acquisition_utc:
            rejections.append({"id": sc.product_id, "reason": "Missing acquisition timestamp."})
            continue

        try:
            sc_dt = parse_iso_dt(sc.acquisition_utc)
        except Exception:
            rejections.append({"id": sc.product_id, "reason": f"Unparseable datetime '{sc.acquisition_utc}'."})
            continue

        if sc.relative_orbit is None:
            rejections.append({"id": sc.product_id, "reason": "Missing relative orbit metadata; pairing unverifiable."})
            continue

        # Check coverage
        sc_box = box(*sc.bounding_box)
        if not sc_box.intersects(aoi_shp):
            rejections.append({"id": sc.product_id, "reason": "Footprint does not intersect AOI."})
            continue

        if sc_dt < event_dt:
            pre_candidates.append(sc)
        else:
            post_candidates.append(sc)

    valid_pairs: List[ScenePair] = []

    # Match pre and post scenes by exact relative orbit, direction, and ~12 day baseline
    for post in post_candidates:
        post_dt = parse_iso_dt(post.acquisition_utc)
        for pre in pre_candidates:
            pre_dt = parse_iso_dt(pre.acquisition_utc)

            # Pair invariant 1: Same relative orbit
            if pre.relative_orbit != post.relative_orbit:
                continue

            # Pair invariant 2: Same orbit direction (ascending / descending)
            if pre.orbit_direction != post.orbit_direction:
                continue

            # Pair invariant 3: Compatible mode
            if pre.instrument_mode != post.instrument_mode:
                continue

            delta_days = (post_dt - pre_dt).total_seconds() / 86400.0

            # Invariant 4: Approximately 12-day repeat (with tolerance)
            # Sentinel-1 repeat orbit cycle is 12 days (or multiples: 12, 24, 36)
            is_valid_repeat = False
            for cycle in [12, 24, 36]:
                if abs(delta_days - cycle) <= tolerance_days:
                    is_valid_repeat = True
                    break

            if not is_valid_repeat:
                continue

            notes = f"Matched track {post.relative_orbit} ({post.orbit_direction}), interval: {delta_days:.1f} days"
            valid_pairs.append(
                ScenePair(
                    pre_scene=pre,
                    post_scene=post,
                    relative_orbit=post.relative_orbit,
                    orbit_direction=post.orbit_direction,
                    interval_days=round(delta_days, 2),
                    valid=True,
                    pairing_notes=notes
                )
            )

    # Sort valid pairs: prefer pairs with earliest post-event acquisition and closest ~12d baseline
    valid_pairs.sort(key=lambda p: (
        parse_iso_dt(p.post_scene.acquisition_utc),
        abs(p.interval_days - pair_interval_days)
    ))

    return valid_pairs, rejections
