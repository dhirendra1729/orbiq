"""Tests for building/road exposure and before/after accessibility routing."""

import networkx as nx
from shapely.geometry import Polygon, LineString, Point
import pytest

from track_b.geo.grid import create_grid_spec
from track_b.geo.exposure import assess_building_exposure, assess_road_exposure
from track_b.geo.road_graph import build_road_graph, build_scenario_graph
from track_b.geo.accessibility import analyze_settlement_accessibility


@pytest.fixture
def sample_grid():
    aoi_poly = {
        "type": "Polygon",
        "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]
    }
    return create_grid_spec(aoi_poly, resolution_m=20.0)


def test_building_exposure_intersection(sample_grid):
    # A building footprint
    bldg_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[85.15, 27.95], [85.16, 27.95], [85.16, 27.96], [85.15, 27.96], [85.15, 27.95]]]
                },
                "properties": {"id": "b1", "name": "Village Hall"}
            }
        ]
    }
    # A water polygon covering the building partially
    water_poly = Polygon([[85.155, 27.95], [85.17, 27.95], [85.17, 27.97], [85.155, 27.97], [85.155, 27.95]])

    res = assess_building_exposure(bldg_geojson, [water_poly], [], sample_grid)
    feat = res["features"][0]
    assert feat["properties"]["exposure_class"] == "water_exposed"
    assert feat["properties"]["water_overlap_m2"] > 0
    assert 0.0 < feat["properties"]["overlap_fraction"] <= 1.0


def test_road_exposure_intersection(sample_grid):
    road_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[85.14, 27.95], [85.18, 27.95]]
                },
                "properties": {"id": "way_1", "highway": "secondary", "bridge": "no"}
            }
        ]
    }
    water_poly = Polygon([[85.15, 27.94], [85.17, 27.94], [85.17, 27.96], [85.15, 27.96], [85.15, 27.94]])

    res = assess_road_exposure(road_geojson, [water_poly], [], sample_grid)
    feat = res["features"][0]
    assert feat["properties"]["exposure_status"] == "exposed"
    assert feat["properties"]["water_overlap_m"] > 0


def test_settlement_cut_off_bottleneck(sample_grid):
    # Network: Settlement S1 -> Node A -(Bridge B)- Node C -> Town T1 / Hospital H1
    # When Bridge B is blocked by flood: S1 loses access and becomes newly_cut_off
    roads_geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[85.12, 27.95], [85.14, 27.95]]},
                "properties": {"id": "w1", "highway": "residential", "is_bridge": False, "blocked_precautionary": False}
            },
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[85.14, 27.95], [85.16, 27.95]]},
                "properties": {"id": "w_bridge", "highway": "primary", "is_bridge": True, "blocked_precautionary": True}
            },
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[85.16, 27.95], [85.18, 27.95]]},
                "properties": {"id": "w2", "highway": "primary", "is_bridge": False, "blocked_precautionary": False}
            }
        ]
    }

    settlements_geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [85.12, 27.95]},
                "properties": {"id": "s1", "name": "Isolated Village", "place": "village"}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [85.18, 27.95]},
                "properties": {"id": "t1", "name": "Market Town", "place": "town"}
            }
        ]
    }

    hospitals_geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [85.18, 27.95]},
                "properties": {"id": "h1", "name": "Regional Hospital"}
            }
        ]
    }

    G_base, node_coords = build_road_graph(roads_geo, sample_grid)
    # Check baseline path exists
    assert nx.number_connected_components(G_base) == 1

    access_res = analyze_settlement_accessibility(
        settlements_geojson=settlements_geo,
        hospitals_geojson=hospitals_geo,
        G_base=G_base,
        node_coords_utm=node_coords,
        grid=sample_grid,
        scenario="precautionary"
    )

    s1_res = [s for s in access_res["settlements"] if s["settlement_id"] == "s1"][0]
    assert s1_res["status_overall"] == "newly_cut_off"
    assert s1_res["status_hospital"] == "newly_cut_off"
