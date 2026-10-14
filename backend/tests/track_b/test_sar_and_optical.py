"""Tests for SAR backscatter processing, Otsu thresholding, and optical debris detection."""

import numpy as np
import pytest

from track_b.geo.flood import refined_lee_filter, linear_to_db, compute_otsu_threshold, detect_inundation
from track_b.geo.debris import detect_candidate_debris, compute_normalized_difference


def test_linear_to_db_conversion():
    power = np.array([0.01, 0.1, 1.0, 0.0, -5.0], dtype=np.float32)
    db = linear_to_db(power)
    assert np.isclose(db[0], -20.0, atol=0.1)
    assert np.isclose(db[1], -10.0, atol=0.1)
    assert np.isclose(db[2], 0.0, atol=0.1)
    assert db[3] == -9999.0
    assert db[4] == -9999.0


def test_otsu_threshold_bimodal():
    # Synthetic bimodal distribution: water (-22 dB) and land (-10 dB)
    np.random.seed(42)
    water_samples = np.random.normal(-22.0, 1.5, 1000)
    land_samples = np.random.normal(-10.0, 2.0, 2000)
    samples = np.concatenate([water_samples, land_samples])

    threshold, var_between = compute_otsu_threshold(samples)
    # The optimal threshold separating -22 and -10 should be roughly in [-18, -14]
    assert -19.0 <= threshold <= -13.0
    assert var_between > 0.0


def test_detect_inundation_permanent_water_subtraction():
    # Grid: 50x50
    # Region 1: Permanent lake (low backscatter in pre and post)
    # Region 2: Newly flooded plain (high backscatter in pre, low in post)
    # Region 3: Dry land (high backscatter in pre and post)
    pre_power = np.full((50, 50), 0.05, dtype=np.float32)  # ~ -13 dB land
    post_power = np.full((50, 50), 0.05, dtype=np.float32)

    # Permanent water (row 0..10, col 0..10): 0.003 (~ -25 dB)
    pre_power[0:10, 0:10] = 0.003
    post_power[0:10, 0:10] = 0.003

    # New flood (row 20..30, col 20..30): was 0.05, became 0.003 in post
    post_power[20:30, 20:30] = 0.003

    valid_mask = np.ones((50, 50), dtype=bool)

    res = detect_inundation(pre_power, post_power, valid_mask, resolution_m=20.0)

    # Permanent lake must be marked as permanent_water, NOT new_water
    assert np.all(res["permanent_water_mask"][1:9, 1:9] == True)
    assert np.all(res["new_water_mask"][1:9, 1:9] == False)

    # Newly flooded area must be marked as new_water
    assert np.all(res["new_water_mask"][22:28, 22:28] == True)
    assert res["new_water_area_m2"] > 0


def test_candidate_debris_detection():
    # Pre-event: high vegetation (NIR=0.5, Red=0.1 -> NDVI ~ 0.66)
    # Post-event: stripped vegetation, sediment (NIR=0.15, Red=0.25 -> NDVI ~ -0.25, SWIR=0.22)
    pre_nir = np.full((20, 20), 0.5, dtype=np.float32)
    pre_red = np.full((20, 20), 0.1, dtype=np.float32)
    pre_swir = np.full((20, 20), 0.1, dtype=np.float32)

    post_nir = np.full((20, 20), 0.15, dtype=np.float32)
    post_red = np.full((20, 20), 0.25, dtype=np.float32)
    post_swir = np.full((20, 20), 0.22, dtype=np.float32)

    water_mask = np.zeros((20, 20), dtype=bool)
    pre_cloud = np.zeros((20, 20), dtype=bool)
    post_cloud = np.zeros((20, 20), dtype=bool)

    res = detect_candidate_debris(
        pre_nir, pre_red, pre_swir,
        post_nir, post_red, post_swir,
        water_mask, pre_cloud, post_cloud,
        delta_ndvi_threshold=-0.25,
        min_swir_reflectance=0.12
    )

    assert np.all(res["candidate_debris_mask"] == True)
    assert res["debris_area_m2"] == 400 * (20 * 20)
