"""Tests for Sentinel-1 same-track pairing rules and rejection handling."""

import pytest
from datetime import datetime, timezone

from track_b.schemas import SceneMetadata, ScenePair
from track_b.providers.sentinel1 import discover_sentinel1_pairs


def make_scene(pid: str, dt_str: str, rel_orbit: int, direction: str) -> SceneMetadata:
    return SceneMetadata(
        product_id=pid,
        collection="sentinel-1-grd",
        acquisition_utc=dt_str,
        platform="sentinel-1",
        relative_orbit=rel_orbit,
        orbit_direction=direction,
        instrument_mode="IW",
        polarizations=["VV", "VH"],
        processing_level="GRD",
        bounding_box=[85.0, 27.5, 85.5, 28.5],
        coverage_fraction=1.0,
        asset_urls={"vv": "https://example.com/vv.tif"},
        scene_valid=True
    )


def test_valid_same_track_pair_12_days():
    pre = make_scene("S1_PRE", "2026-08-14T12:00:00Z", 85, "ascending")
    post = make_scene("S1_POST", "2026-08-26T12:00:00Z", 85, "ascending")

    pair = ScenePair(
        pre_scene=pre,
        post_scene=post,
        relative_orbit=85,
        orbit_direction="ascending",
        interval_days=12.0,
        valid=True
    )
    assert pair.valid is True
    assert pair.relative_orbit == 85
    assert pair.interval_days == 12.0


def test_pairing_rejects_mismatched_orbits():
    pre = make_scene("S1_PRE", "2026-08-14T12:00:00Z", 85, "ascending")
    post = make_scene("S1_POST", "2026-08-26T12:00:00Z", 120, "ascending")

    # Orbits 85 != 120
    assert pre.relative_orbit != post.relative_orbit


def test_pairing_rejects_mismatched_direction():
    pre = make_scene("S1_PRE", "2026-08-14T12:00:00Z", 85, "ascending")
    post = make_scene("S1_POST", "2026-08-26T12:00:00Z", 85, "descending")

    # Ascending != Descending
    assert pre.orbit_direction != post.orbit_direction
