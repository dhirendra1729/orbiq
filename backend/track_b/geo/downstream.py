"""DEM-derived downstream drainage path tracing and affected settlement corridor bonus."""

from typing import Any, Dict, List, Optional, Tuple
import math
import numpy as np
from shapely.geometry import shape, Point, LineString, Polygon, mapping
import pyproj

from track_b.schemas import GridSpec


def trace_d8_downstream(
    dem: np.ndarray,
    seed_row: int,
    seed_col: int,
    resolution_m: float = 20.0,
    max_steps: int = 5000
) -> List[Tuple[int, int]]:
    """Trace downstream path using D8 steepest descent flow direction on DEM."""
    height, width = dem.shape
    curr_r, curr_c = seed_row, seed_col
    path = [(curr_r, curr_c)]
    visited = set(path)

    # 8-neighbor offsets and distances
    # Directions: (dr, dc, distance)
    d8_moves = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
        (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))
    ]

    for _ in range(max_steps):
        curr_elev = dem[curr_r, curr_c]
        best_r, best_c = None, None
        max_slope = 0.0

        for dr, dc, dist in d8_moves:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < height and 0 <= nc < width:
                neighbor_elev = dem[nr, nc]
                if neighbor_elev != -9999.0 and not np.isnan(neighbor_elev):
                    drop = curr_elev - neighbor_elev
                    slope = drop / (dist * resolution_m)
                    if slope > max_slope:
                        max_slope = slope
                        best_r, best_c = nr, nc

        if best_r is None or (best_r, best_c) in visited:
            # Reached a sink, flat area, or grid boundary
            break

        curr_r, curr_c = best_r, best_c
        path.append((curr_r, curr_c))
        visited.add((curr_r, curr_c))

    return path


def compute_downstream_corridor(
    upstream_lon: float,
    upstream_lat: float,
    dem_array: np.ndarray,
    grid: GridSpec,
    settlements_geojson: Dict[str, Any],
    corridor_buffer_m: float = 1000.0
) -> Dict[str, Any]:
    """Calculate the DEM downstream drainage path from an upstream point and list settlements in its corridor."""
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True)
    transformer_to_wgs = pyproj.Transformer.from_crs(grid.crs, "EPSG:4326", always_xy=True)

    ux, uy = transformer_to_utm.transform(upstream_lon, upstream_lat)
    minx, miny, maxx, maxy = grid.bounds_projected

    # Convert coordinates to pixel row and column
    col = int(round((ux - minx) / grid.resolution_m))
    row = int(round((maxy - uy) / grid.resolution_m))

    col = max(0, min(grid.width - 1, col))
    row = max(0, min(grid.height - 1, row))

    path_pixels = trace_d8_downstream(dem_array, row, col, resolution_m=grid.resolution_m)

    # Convert pixel path to UTM coordinates
    utm_path_coords = [
        (minx + c * grid.resolution_m, maxy - r * grid.resolution_m)
        for r, c in path_pixels
    ]

    if len(utm_path_coords) < 2:
        return {
            "type": "FeatureCollection",
            "features": [],
            "message": "Downstream flow path could not be traced beyond initial point (local terrain sink)."
        }

    path_line_utm = LineString(utm_path_coords)
    corridor_poly_utm = path_line_utm.buffer(corridor_buffer_m)

    # Transform back to WGS84
    wgs_coords = [transformer_to_wgs.transform(x, y) for x, y in utm_path_coords]
    path_line_wgs = LineString(wgs_coords)

    # Convert corridor polygon to WGS84
    from shapely.ops import transform
    corridor_poly_wgs = transform(transformer_to_wgs.transform, corridor_poly_utm)

    # Identify settlements inside the downstream corridor
    corridor_settlements = []
    for s_feat in settlements_geojson.get("features", []):
        s_geom = shape(s_feat.get("geometry"))
        if corridor_poly_wgs.contains(s_geom):
            props = s_feat.get("properties", {})
            dist_to_path = path_line_wgs.distance(s_geom) * 111000.0  # approximate metres
            corridor_settlements.append({
                "id": str(props.get("@id") or props.get("id")),
                "name": props.get("name", "Unnamed settlement"),
                "place": props.get("place", "village"),
                "approx_distance_to_flow_path_m": round(dist_to_path, 1),
                "coordinates": [s_geom.x, s_geom.y]
            })

    corridor_settlements.sort(key=lambda s: s["approx_distance_to_flow_path_m"])

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": mapping(path_line_wgs),
                "properties": {
                    "type": "dem_derived_drainage_path",
                    "total_length_km": round(path_line_utm.length / 1000.0, 2),
                    "steps": len(path_pixels),
                    "disclaimer": "DEM-derived gravity flow path. Does not model fluid dynamics, breach volume or sediment transport."
                }
            },
            {
                "type": "Feature",
                "geometry": mapping(corridor_poly_wgs),
                "properties": {
                    "type": "corridor_buffer",
                    "buffer_radius_m": corridor_buffer_m,
                    "settlements_count": len(corridor_settlements)
                }
            }
        ],
        "corridor_settlements": corridor_settlements
    }
