"""Tests for coordinate transformations, dynamic UTM grid, and slope masking."""

import numpy as np
import pytest

from track_b.geo.grid import get_utm_epsg, create_grid_spec
from track_b.geo.masks import compute_terrain_slope_degrees, generate_terrain_uncertainty_mask


def test_utm_epsg_nepal():
    # Trishuli River, Nepal: lon 85.2, lat 28.0 -> UTM Zone 45 North (EPSG:32645)
    epsg = get_utm_epsg(85.2, 28.0)
    assert epsg == 32645


def test_utm_epsg_southern_hemisphere():
    epsg = get_utm_epsg(151.2, -33.9)  # Sydney -> Zone 56 South (EPSG:32756)
    assert epsg == 32756


def test_create_grid_spec():
    aoi_poly = {
        "type": "Polygon",
        "coordinates": [[[85.1, 27.9], [85.3, 27.9], [85.3, 28.1], [85.1, 28.1], [85.1, 27.9]]]
    }
    grid = create_grid_spec(aoi_poly, resolution_m=20.0)
    assert grid.crs == "EPSG:32645"
    assert grid.resolution_m == 20.0
    assert grid.width > 0
    assert grid.height > 0
    assert len(grid.transform) == 6


def test_slope_calculation():
    # 1. Flat terrain: slope = 0
    flat_dem = np.full((10, 10), 500.0, dtype=np.float32)
    slope_deg, valid = compute_terrain_slope_degrees(flat_dem, resolution_m=20.0)
    assert np.allclose(slope_deg[1:-1, 1:-1], 0.0, atol=1e-4)

    # 2. 45-degree slope (rise 20m per 20m horizontal step)
    ramp_dem = np.zeros((10, 10), dtype=np.float32)
    for r in range(10):
        ramp_dem[r, :] = r * 20.0  # gradient in y direction = 20m / 20m = 1.0 -> arctan(1.0) = 45 deg

    slope_ramp, _ = compute_terrain_slope_degrees(ramp_dem, resolution_m=20.0)
    assert np.allclose(slope_ramp[1:-1, 1:-1], 45.0, atol=1.0)


def test_terrain_uncertainty_mask():
    dem = np.zeros((10, 10), dtype=np.float32)
    # Steep slope in top half, flat in bottom half
    for r in range(5):
        dem[r, :] = r * 30.0  # slope > 20 deg
    for r in range(5, 10):
        dem[r, :] = 150.0  # flat

    uncertain = generate_terrain_uncertainty_mask(dem, resolution_m=20.0, slope_threshold_deg=20.0)
    assert np.any(uncertain[1:4, 1:9])
    assert not np.any(uncertain[6:9, 1:9])
