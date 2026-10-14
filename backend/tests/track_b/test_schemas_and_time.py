"""Tests for requests, time invariants, and schema validation."""

import pytest
from pydantic import ValidationError

from track_b.schemas import AOIGeometry, TrackBRequest
from track_b.providers.ohsome import determine_effective_osm_snapshot


def test_valid_aoi_geometry():
    poly = {
        "type": "Polygon",
        "coordinates": [[[85.1, 27.9], [85.2, 27.9], [85.2, 28.0], [85.1, 28.0], [85.1, 27.9]]]
    }
    geom = AOIGeometry.model_validate(poly)
    assert geom.type == "Polygon"
    assert len(geom.coordinates[0]) == 5


def test_unclosed_aoi_geometry_is_auto_closed():
    unclosed = {
        "type": "Polygon",
        "coordinates": [[[85.1, 27.9], [85.2, 27.9], [85.2, 28.0], [85.1, 28.0]]]
    }
    geom = AOIGeometry.model_validate(unclosed)
    assert geom.coordinates[0][0] == geom.coordinates[0][-1]


def test_invalid_coordinates_range_rejected():
    invalid_lon = {
        "type": "Polygon",
        "coordinates": [[[195.0, 27.9], [85.2, 27.9], [85.2, 28.0], [195.0, 27.9]]]
    }
    with pytest.raises(ValidationError):
        AOIGeometry.model_validate(invalid_lon)


def test_invalid_event_date_rejected():
    poly = {
        "type": "Polygon",
        "coordinates": [[[85.1, 27.9], [85.2, 27.9], [85.2, 28.0], [85.1, 28.0], [85.1, 27.9]]]
    }
    with pytest.raises(ValidationError):
        TrackBRequest(aoi=poly, event_date="not-a-date")


def test_effective_osm_snapshot_strictly_pre_event():
    event_date = "2026-08-26"
    effective_ts, prov = determine_effective_osm_snapshot(event_date)
    # Must be prior to event date
    assert effective_ts <= "2026-08-25T23:59:59Z"
    assert prov["snapshot_age_at_event_days"] > 0


def test_explicit_post_event_osm_timestamp_rejected():
    event_date = "2026-08-26"
    # An explicit timestamp on or after the event date must fail
    with pytest.raises(ValueError, match="violates pre-event invariant"):
        determine_effective_osm_snapshot(event_date, user_explicit_timestamp="2026-08-27T00:00:00Z")
