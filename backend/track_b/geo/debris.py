"""Candidate debris and sediment deposition detection using multispectral optical change and valley corridors."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
from shapely.geometry import shape, mapping, Polygon
import rasterio.features
from rasterio.transform import Affine
import pyproj

from track_b.schemas import GridSpec


def compute_normalized_difference(b1: np.ndarray, b2: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Compute normalized difference index (b1 - b2) / (b1 + b2)."""
    denom = b1 + b2
    valid = (~np.isnan(b1)) & (~np.isnan(b2)) & (np.abs(denom) > eps)
    out = np.full_like(b1, np.nan, dtype=np.float32)
    out[valid] = (b1[valid] - b2[valid]) / denom[valid]
    return out


def detect_candidate_debris(
    pre_nir: np.ndarray,
    pre_red: np.ndarray,
    pre_swir: np.ndarray,
    post_nir: np.ndarray,
    post_red: np.ndarray,
    post_swir: np.ndarray,
    water_mask: np.ndarray,
    pre_cloud_mask: np.ndarray,
    post_cloud_mask: np.ndarray,
    valley_corridor_mask: Optional[np.ndarray] = None,
    delta_ndvi_threshold: float = -0.25,
    min_swir_reflectance: float = 0.12,
    resolution_m: float = 20.0,
    min_area_m2: float = 400.0
) -> Dict[str, Any]:
    """Identify candidate debris flows from clear optical pairs along drainage corridors.

    Returns:
        {
            "candidate_debris_mask": np.ndarray,
            "optical_valid_mask": np.ndarray,
            "delta_ndvi": np.ndarray,
            "debris_area_m2": float,
            "unassessed_cloud_area_m2": float
        }
    """
    # 1. Determine clear optical validity
    clear_optical = (~pre_cloud_mask) & (~post_cloud_mask)

    # 2. Compute pre and post NDVI
    pre_ndvi = compute_normalized_difference(pre_nir, pre_red)
    post_ndvi = compute_normalized_difference(post_nir, post_red)
    delta_ndvi = np.where(clear_optical, post_ndvi - pre_ndvi, np.nan)

    # 3. Detect sharp vegetation loss with high bare earth/sediment SWIR reflectance
    raw_debris = (
        clear_optical &
        (delta_ndvi <= delta_ndvi_threshold) &
        (post_swir >= min_swir_reflectance) &
        (~water_mask)
    )

    # 4. Filter to drainage/valley corridor if provided
    if valley_corridor_mask is not None:
        candidate_debris = raw_debris & valley_corridor_mask
    else:
        candidate_debris = raw_debris

    pixel_area_m2 = resolution_m * resolution_m
    debris_area = float(np.sum(candidate_debris) * pixel_area_m2)
    cloud_area = float(np.sum(~clear_optical) * pixel_area_m2)

    return {
        "candidate_debris_mask": candidate_debris,
        "optical_valid_mask": clear_optical,
        "delta_ndvi": delta_ndvi,
        "debris_area_m2": debris_area,
        "unassessed_cloud_area_m2": cloud_area
    }
