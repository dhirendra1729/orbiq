"""Dynamic UTM CRS selection, raster grid definition, and reprojection helpers."""

import math
from typing import Any, Dict, List, Tuple
import numpy as np
from shapely.geometry import shape, mapping, box
import pyproj
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling

from track_b.schemas import GridSpec


def get_utm_epsg(lon: float, lat: float) -> int:
    """Calculate the UTM EPSG code from longitude and latitude."""
    zone = int(math.floor((lon + 180.0) / 6.0)) + 1
    if lat >= 0:
        return 32600 + zone
    else:
        return 32700 + zone


def get_aoi_bounds_wgs84(aoi_geom: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Return (minx, miny, maxx, maxy) in EPSG:4326."""
    geom = shape(aoi_geom)
    return geom.bounds


def create_grid_spec(
    aoi_geom: Dict[str, Any],
    resolution_m: float = 20.0,
    buffer_m: float = 0.0
) -> GridSpec:
    """Compute the unified projected metric grid for the analysis run."""
    geom_wgs = shape(aoi_geom)
    minx, miny, maxx, maxy = geom_wgs.bounds
    centroid_lon = (minx + maxx) / 2.0
    centroid_lat = (miny + maxy) / 2.0

    epsg_code = get_utm_epsg(centroid_lon, centroid_lat)
    target_crs = f"EPSG:{epsg_code}"

    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    transformer_to_wgs = pyproj.Transformer.from_crs(target_crs, "EPSG:4326", always_xy=True)

    # Project the bounding box corners to metric UTM
    poly_pts = [
        (minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)
    ]
    utm_pts = [transformer_to_utm.transform(x, y) for x, y in poly_pts]
    xs = [p[0] for p in utm_pts]
    ys = [p[1] for p in utm_pts]

    utm_minx = min(xs) - buffer_m
    utm_miny = min(ys) - buffer_m
    utm_maxx = max(xs) + buffer_m
    utm_maxy = max(ys) + buffer_m

    # Align to grid resolution
    utm_minx = math.floor(utm_minx / resolution_m) * resolution_m
    utm_miny = math.floor(utm_miny / resolution_m) * resolution_m
    utm_maxx = math.ceil(utm_maxx / resolution_m) * resolution_m
    utm_maxy = math.ceil(utm_maxy / resolution_m) * resolution_m

    width = int(round((utm_maxx - utm_minx) / resolution_m))
    height = int(round((utm_maxy - utm_miny) / resolution_m))

    # Affine transform for rasterio: west, south, east, north
    # Affine from bounds: (left, bottom, right, top, width, height)
    affine_trans = from_bounds(utm_minx, utm_miny, utm_maxx, utm_maxy, width, height)
    trans_list = [
        affine_trans.a, affine_trans.b, affine_trans.c,
        affine_trans.d, affine_trans.e, affine_trans.f
    ]

    # Convert buffered metric bounds back to WGS84
    wgs_sw = transformer_to_wgs.transform(utm_minx, utm_miny)
    wgs_ne = transformer_to_wgs.transform(utm_maxx, utm_maxy)
    wgs_bounds = (wgs_sw[0], wgs_sw[1], wgs_ne[0], wgs_ne[1])

    zone_num = epsg_code - (32600 if centroid_lat >= 0 else 32700)

    return GridSpec(
        crs=target_crs,
        utm_zone=zone_num,
        resolution_m=resolution_m,
        bounds_projected=(utm_minx, utm_miny, utm_maxx, utm_maxy),
        bounds_wgs84=wgs_bounds,
        width=width,
        height=height,
        transform=trans_list,
    )


def warp_raster_to_grid(
    src_array: np.ndarray,
    src_crs: str,
    src_transform: Any,
    grid: GridSpec,
    resampling: Resampling = Resampling.bilinear,
    src_nodata: float = -9999.0,
    dst_nodata: float = -9999.0
) -> np.ndarray:
    """Reproject a raster array to the run grid."""
    from affine import Affine
    dst_transform = Affine(*grid.transform)
    dst_array = np.full((grid.height, grid.width), dst_nodata, dtype=src_array.dtype)

    reproject(
        source=src_array,
        destination=dst_array,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=grid.crs,
        resampling=resampling,
        src_nodata=src_nodata,
        dst_nodata=dst_nodata
    )
    return dst_array
