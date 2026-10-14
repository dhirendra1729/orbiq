"""Asset exposure intersection analysis for buildings, roads, and bridges."""

from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import geopandas as gpd
import pandas as pd
import pyproj

from track_b.schemas import GridSpec


def assess_building_exposure(
    buildings_geojson: Dict[str, Any],
    water_polygons: List[Any],
    debris_polygons: List[Any],
    grid: GridSpec
) -> Dict[str, Any]:
    """Calculate geometric intersection of building footprints with flood water and candidate debris.

    Returns:
        GeoJSON FeatureCollection with per-building exposure metrics and summary statistics.
    """
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)

    # Union all water and debris geometries for fast spatial querying
    all_water = unary_union(water_polygons) if water_polygons else None
    all_debris = unary_union(debris_polygons) if debris_polygons else None

    features = []
    total_buildings = 0
    exposed_water_count = 0
    exposed_debris_count = 0
    exposed_mixed_count = 0
    total_exposed_area_m2 = 0.0

    raw_features = buildings_geojson.get("features", [])
    for idx, feat in enumerate(raw_features):
        bldg_geom = shape(feat.get("geometry"))
        if not bldg_geom.is_valid:
            bldg_geom = bldg_geom.buffer(0)
        if bldg_geom.is_empty:
            continue

        total_buildings += 1
        props = feat.get("properties", {})
        osm_id = props.get("@id") or props.get("id") or f"bldg_{idx}"
        bldg_name = props.get("name", "")

        # Compute metric area
        # Project geometry to UTM
        from shapely.ops import transform
        bldg_utm = transform(transformer_to_utm.transform, bldg_geom)
        footprint_area_m2 = round(bldg_utm.area, 2)

        water_overlap_m2 = 0.0
        debris_overlap_m2 = 0.0

        if all_water and bldg_geom.intersects(all_water):
            inter = bldg_geom.intersection(all_water)
            inter_utm = transform(transformer_to_utm.transform, inter)
            water_overlap_m2 = round(inter_utm.area, 2)

        if all_debris and bldg_geom.intersects(all_debris):
            inter_d = bldg_geom.intersection(all_debris)
            inter_d_utm = transform(transformer_to_utm.transform, inter_d)
            debris_overlap_m2 = round(inter_d_utm.area, 2)

        overlap_fraction = 0.0
        if footprint_area_m2 > 0:
            overlap_fraction = round(min(1.0, (water_overlap_m2 + debris_overlap_m2) / footprint_area_m2), 3)

        if water_overlap_m2 > 0 and debris_overlap_m2 > 0:
            exp_class = "mixed_exposure"
            exposed_mixed_count += 1
            total_exposed_area_m2 += water_overlap_m2 + debris_overlap_m2
        elif water_overlap_m2 > 0:
            exp_class = "water_exposed"
            exposed_water_count += 1
            total_exposed_area_m2 += water_overlap_m2
        elif debris_overlap_m2 > 0:
            exp_class = "candidate_debris_exposed"
            exposed_debris_count += 1
            total_exposed_area_m2 += debris_overlap_m2
        else:
            exp_class = "no_mapped_overlap"

        features.append({
            "type": "Feature",
            "geometry": mapping(bldg_geom),
            "properties": {
                "id": str(osm_id),
                "name": bldg_name,
                "exposure_class": exp_class,
                "footprint_area_m2": footprint_area_m2,
                "water_overlap_m2": water_overlap_m2,
                "debris_overlap_m2": debris_overlap_m2,
                "overlap_fraction": overlap_fraction,
                "amenity": props.get("amenity", "")
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "total_buildings": total_buildings,
            "exposed_water_count": exposed_water_count,
            "exposed_debris_count": exposed_debris_count,
            "exposed_mixed_count": exposed_mixed_count,
            "total_exposed_count": exposed_water_count + exposed_debris_count + exposed_mixed_count,
            "total_exposed_footprint_m2": round(total_exposed_area_m2, 2)
        }
    }


def assess_road_exposure(
    roads_geojson: Dict[str, Any],
    water_polygons: List[Any],
    debris_polygons: List[Any],
    grid: GridSpec
) -> Dict[str, Any]:
    """Calculate metric line intersection length for road segments with water and debris."""
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)
    from shapely.ops import transform

    all_water = unary_union(water_polygons) if water_polygons else None
    all_debris = unary_union(debris_polygons) if debris_polygons else None

    features = []
    total_roads = 0
    total_length_m = 0.0
    flooded_length_m = 0.0
    debris_length_m = 0.0
    exposed_ways_count = 0

    raw_features = roads_geojson.get("features", [])
    for idx, feat in enumerate(raw_features):
        road_geom = shape(feat.get("geometry"))
        if road_geom.is_empty:
            continue

        props = feat.get("properties", {})
        way_id = props.get("@id") or props.get("id") or f"way_{idx}"
        highway_type = props.get("highway", "unclassified")
        bridge_tag = props.get("bridge", "no") == "yes"

        road_utm = transform(transformer_to_utm.transform, road_geom)
        length_m = round(road_utm.length, 2)
        total_length_m += length_m
        total_roads += 1

        water_overlap_m = 0.0
        debris_overlap_m = 0.0

        if all_water and road_geom.intersects(all_water):
            inter = road_geom.intersection(all_water)
            inter_utm = transform(transformer_to_utm.transform, inter)
            water_overlap_m = round(inter_utm.length, 2)

        if all_debris and road_geom.intersects(all_debris):
            inter_d = road_geom.intersection(all_debris)
            inter_d_utm = transform(transformer_to_utm.transform, inter_d)
            debris_overlap_m = round(inter_d_utm.length, 2)

        if water_overlap_m > 0 or debris_overlap_m > 0:
            exposed_ways_count += 1
            flooded_length_m += water_overlap_m
            debris_length_m += debris_overlap_m
            exp_status = "exposed"
        else:
            exp_status = "clear"

        features.append({
            "type": "Feature",
            "geometry": mapping(road_geom),
            "properties": {
                "id": str(way_id),
                "name": props.get("name", ""),
                "highway": highway_type,
                "is_bridge": bridge_tag,
                "length_m": length_m,
                "water_overlap_m": water_overlap_m,
                "debris_overlap_m": debris_overlap_m,
                "exposure_status": exp_status,
                "blocked_optimistic": (water_overlap_m > 10.0 or debris_overlap_m > 10.0) and not bridge_tag,
                "blocked_precautionary": (water_overlap_m > 5.0 or debris_overlap_m > 5.0)
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "total_ways_evaluated": total_roads,
            "total_network_length_km": round(total_length_m / 1000.0, 2),
            "exposed_ways_count": exposed_ways_count,
            "water_exposed_length_km": round(flooded_length_m / 1000.0, 2),
            "debris_exposed_length_km": round(debris_length_m / 1000.0, 2),
            "total_exposed_length_km": round((flooded_length_m + debris_length_m) / 1000.0, 2)
        }
    }
