"""SAR backscatter filtering, Otsu thresholding, change detection, and vectorization."""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.ndimage import uniform_filter
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
import rasterio.features
from rasterio.transform import Affine
import pyproj

from track_b.schemas import GridSpec


def refined_lee_filter(image: np.ndarray, window_size: int = 7) -> np.ndarray:
    """Apply Refined Lee speckle filter on linear backscatter power.

    Speckle is multiplicative, so filtering must occur in linear power before
    converting to decibels (dB).
    """
    valid = (image > 0) & (~np.isnan(image))
    if not np.any(valid):
        return image.copy()

    img = np.where(valid, image, 0.0)

    # Calculate local mean and variance
    mean = uniform_filter(img, size=window_size)
    mean_sq = uniform_filter(img ** 2, size=window_size)
    var = np.maximum(0.0, mean_sq - mean ** 2)

    # Noise variance estimate (relative variance for 1-look or multi-look SAR)
    overall_mean = np.mean(img[valid])
    overall_var = np.var(img[valid])
    if overall_mean > 0:
        cu = math.sqrt(max(1e-6, overall_var)) / overall_mean
    else:
        cu = 0.523  # Standard theoretical 1-look speckle coefficient of variation
    cu_sq = cu ** 2

    # Weight factor
    mean_sq_safe = np.maximum(1e-8, mean ** 2)
    ci_sq = np.where(mean > 0, var / mean_sq_safe, 0.0)
    w = np.where(ci_sq > cu_sq, (ci_sq - cu_sq) / (ci_sq * (1.0 + cu_sq) + 1e-8), 0.0)
    w = np.clip(w, 0.0, 1.0)

    filtered = mean + w * (img - mean)
    filtered = np.where(valid, np.maximum(1e-7, filtered), 0.0)
    return filtered


def linear_to_db(power: np.ndarray) -> np.ndarray:
    """Convert positive linear backscatter power to decibels (dB)."""
    valid = (power > 0) & (~np.isnan(power))
    db = np.full_like(power, -9999.0, dtype=np.float32)
    db[valid] = 10.0 * np.log10(power[valid])
    return db


def compute_otsu_threshold(values_db: np.ndarray, min_val: float = -35.0, max_val: float = 0.0) -> Tuple[float, float]:
    """Compute Otsu's threshold on decibel backscatter.

    Returns:
        (optimal_threshold_db, between_class_variance)
    """
    valid = (values_db >= min_val) & (values_db <= max_val) & (~np.isnan(values_db))
    samples = values_db[valid]
    if len(samples) < 100:
        return -16.0, 0.0  # Fallback standard radar water threshold in dB

    # 256-bin histogram
    hist, bin_edges = np.histogram(samples, bins=256, range=(min_val, max_val))
    total_pixels = len(samples)
    current_max = 0.0
    threshold = -16.0

    sum_total = np.sum(np.arange(256) * hist)
    sum_b = 0.0
    w_b = 0.0

    for i in range(256):
        w_b += hist[i]
        if w_b == 0:
            continue
        w_f = total_pixels - w_b
        if w_f == 0:
            break

        sum_b += i * hist[i]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f

        # Between-class variance
        var_between = w_b * w_f * ((m_b - m_f) ** 2)

        if var_between > current_max:
            current_max = var_between
            threshold = (bin_edges[i] + bin_edges[i + 1]) / 2.0

    return float(threshold), float(current_max)


def detect_inundation(
    pre_power: np.ndarray,
    post_power: np.ndarray,
    valid_domain_mask: np.ndarray,
    terrain_uncertain_mask: Optional[np.ndarray] = None,
    min_area_m2: float = 400.0,
    resolution_m: float = 20.0
) -> Dict[str, Any]:
    """Execute Sentinel-1 change detection between matched pre and post power rasters.

    Returns:
        {
            "pre_water_mask": np.ndarray,
            "post_water_mask": np.ndarray,
            "new_water_mask": np.ndarray,
            "permanent_water_mask": np.ndarray,
            "db_change": np.ndarray,
            "pre_threshold_db": float,
            "post_threshold_db": float,
            "new_water_area_m2": float,
            "permanent_water_area_m2": float
        }
    """
    # 1. Filter in linear power
    pre_filt = refined_lee_filter(pre_power)
    post_filt = refined_lee_filter(post_power)

    # 2. Convert to dB
    pre_db = linear_to_db(pre_filt)
    post_db = linear_to_db(post_filt)

    # 3. Calculate thresholds
    pre_thresh, _ = compute_otsu_threshold(pre_db[valid_domain_mask])
    post_thresh, _ = compute_otsu_threshold(post_db[valid_domain_mask])

    # 4. Initial water masks
    pre_water = (pre_db <= pre_thresh) & valid_domain_mask & (pre_db > -40.0)
    post_water = (post_db <= post_thresh) & valid_domain_mask & (post_db > -40.0)

    # 5. Remove terrain-uncertain mountain shadow pixels if provided
    if terrain_uncertain_mask is not None:
        pre_water = pre_water & (~terrain_uncertain_mask)
        post_water = post_water & (~terrain_uncertain_mask)

    # 6. Change subtraction: new inundation vs permanent water
    permanent_water = pre_water & post_water
    new_water = post_water & (~pre_water)

    # Backscatter difference: Delta = B_post - B_pre
    db_change = np.where(valid_domain_mask, post_db - pre_db, np.nan)

    # Calculate pixel areas
    pixel_area_m2 = resolution_m * resolution_m
    new_water_area = float(np.sum(new_water) * pixel_area_m2)
    perm_water_area = float(np.sum(permanent_water) * pixel_area_m2)

    return {
        "pre_water_mask": pre_water,
        "post_water_mask": post_water,
        "new_water_mask": new_water,
        "permanent_water_mask": permanent_water,
        "db_change": db_change,
        "pre_threshold_db": pre_thresh,
        "post_threshold_db": post_thresh,
        "new_water_area_m2": new_water_area,
        "permanent_water_area_m2": perm_water_area
    }


def mask_to_geojson_multipolygon(
    binary_mask: np.ndarray,
    grid: GridSpec,
    min_area_m2: float = 400.0
) -> Dict[str, Any]:
    """Vectorize a binary raster mask into an EPSG:4326 GeoJSON FeatureCollection."""
    pixel_area_m2 = grid.resolution_m * grid.resolution_m
    min_pixels = max(1, int(round(min_area_m2 / pixel_area_m2)))

    transform = Affine(*grid.transform)
    shapes = rasterio.features.shapes(
        binary_mask.astype(np.uint8),
        mask=binary_mask,
        transform=transform
    )

    transformer = pyproj.Transformer.from_crs(grid.crs, "EPSG:4326", always_xy=True)

    features = []
    for geom_dict, val in shapes:
        if val != 1:
            continue
        poly = shape(geom_dict)
        if poly.area < (min_pixels * pixel_area_m2):
            continue

        # Transform coordinates to WGS84
        def reproject_ring(ring):
            return [list(transformer.transform(x, y)) for x, y in ring.coords]

        if poly.geom_type == "Polygon":
            exterior = reproject_ring(poly.exterior)
            interiors = [reproject_ring(interior) for interior in poly.interiors]
            wgs_poly = Polygon(exterior, interiors)
        else:
            continue

        features.append({
            "type": "Feature",
            "geometry": mapping(wgs_poly),
            "properties": {
                "area_m2": round(poly.area, 2)
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
