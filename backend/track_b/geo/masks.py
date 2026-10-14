"""Terrain slope calculation, optical cloud masking, and valid data domain masks."""

import numpy as np
from typing import Optional, Tuple


def compute_terrain_slope_degrees(
    dem_array: np.ndarray,
    resolution_m: float = 20.0,
    nodata_val: float = -9999.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate terrain slope in degrees using 2D finite-difference gradient.

    Returns:
        (slope_degrees, valid_dem_mask)
    """
    valid_mask = (dem_array != nodata_val) & ~np.isnan(dem_array)
    # Fill nodata temporarily with median for gradient calculation
    clean_dem = np.where(valid_mask, dem_array, np.median(dem_array[valid_mask]) if np.any(valid_mask) else 0.0)

    gy, gx = np.gradient(clean_dem, resolution_m)
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_deg = np.degrees(slope_rad)
    slope_deg[~valid_mask] = np.nan

    return slope_deg, valid_mask


def generate_terrain_uncertainty_mask(
    dem_array: np.ndarray,
    resolution_m: float = 20.0,
    slope_threshold_deg: float = 20.0,
    nodata_val: float = -9999.0
) -> np.ndarray:
    """Flag steep mountain slopes where radar shadow/layover causes false water signatures.

    Returns a boolean mask where True = uncertain terrain.
    """
    slope_deg, valid_mask = compute_terrain_slope_degrees(dem_array, resolution_m, nodata_val)
    uncertain = (~valid_mask) | (slope_deg >= slope_threshold_deg)
    return uncertain


def generate_optical_cloud_mask(
    scl_array: np.ndarray,
    cloud_classes: Tuple[int, ...] = (0, 3, 8, 9, 10, 11)
) -> np.ndarray:
    """Mask cloudy, shadowed, snow-covered or nodata pixels from Sentinel-2 SCL.

    Classes from ESA Sentinel-2 SCL:
    0: No data
    1: Saturated or defective
    2: Dark area pixels
    3: Cloud shadows
    8: Cloud medium probability
    9: Cloud high probability
    10: Thin cirrus
    11: Snow or ice

    Returns a boolean mask where True = cloud/shadow/invalid (UNKNOWN).
    """
    mask = np.isin(scl_array, cloud_classes) | (scl_array == -9999) | np.isnan(scl_array)
    return mask
