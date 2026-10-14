"""Sentinel-1 SAR preprocessing pipeline: SNAP GPT workflow and verified COG/GeoTIFF raster adapter."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from affine import Affine

from track_b.config import settings
from track_b.schemas import GridSpec


def is_snap_installed() -> Tuple[bool, Optional[str]]:
    """Check if ESA SNAP Graph Processing Tool (gpt) is available in PATH."""
    gpt_path = shutil.which("gpt")
    if gpt_path:
        return True, gpt_path
    return False, None


def generate_snap_s1_graph_xml(
    input_safe_path: str,
    output_dim_path: str,
    dem_name: str = "Copernicus 30m Global DEM"
) -> str:
    """Generate SNAP XML graph for Sentinel-1 GRD calibration and terrain correction."""
    return f"""<graph id="S1_GRD_Preprocess">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters>
      <file>{input_safe_path}</file>
    </parameters>
  </node>
  <node id="Apply-Orbit-File">
    <operator>Apply-Orbit-File</operator>
    <sources>
      <sourceProduct refid="Read"/>
    </sources>
    <parameters>
      <orbitType>Sentinel Precise (Auto Download)</orbitType>
      <polyDegree>3</polyDegree>
      <continueOnFail>true</continueOnFail>
    </parameters>
  </node>
  <node id="ThermalNoiseRemoval">
    <operator>ThermalNoiseRemoval</operator>
    <sources>
      <sourceProduct refid="Apply-Orbit-File"/>
    </sources>
    <parameters>
      <selectedPolarisations>VV,VH</selectedPolarisations>
      <removeThermalNoise>true</removeThermalNoise>
    </parameters>
  </node>
  <node id="Calibration">
    <operator>Calibration</operator>
    <sources>
      <sourceProduct refid="ThermalNoiseRemoval"/>
    </sources>
    <parameters>
      <sourceBands>Intensity_VV,Intensity_VH</sourceBands>
      <outputGammaBand>true</outputGammaBand>
      <outputSigmaBand>false</outputSigmaBand>
    </parameters>
  </node>
  <node id="Terrain-Correction">
    <operator>Terrain-Correction</operator>
    <sources>
      <sourceProduct refid="Calibration"/>
    </sources>
    <parameters>
      <demName>{dem_name}</demName>
      <pixelSpacingInMeter>20.0</pixelSpacingInMeter>
      <mapProjection>WGS84(DD)</mapProjection>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="Terrain-Correction"/>
    </sources>
    <parameters>
      <file>{output_dim_path}</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
</graph>"""


def preprocess_sar_raster(
    raster_url_or_path: str,
    grid: GridSpec,
    output_tif_path: Optional[Path] = None,
    linear_power: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Read a Sentinel-1 VV backscatter raster, reproject to run grid, and return linear power.

    Returns:
        (power_array, valid_mask)
    """
    with rasterio.open(raster_url_or_path) as src:
        src_crs = src.crs
        src_transform = src.transform
        src_nodata = src.nodata if src.nodata is not None else 0.0

        dst_transform = Affine(*grid.transform)
        dst_array = np.full((grid.height, grid.width), 0.0, dtype=np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=dst_array,
            src_transform=src_transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=grid.crs,
            resampling=Resampling.bilinear,
            src_nodata=src_nodata,
            dst_nodata=0.0
        )

    # Valid mask where backscatter is positive and non-zero
    valid_mask = (dst_array > 0.0) & (~np.isnan(dst_array)) & (dst_array < 1e6)

    # If input is in digital numbers (DN), convert DN to approximate calibrated linear power
    # Standard Sentinel-1 calibration LUT approximate: sigma0 = DN^2 / (A_sigma^2)
    # If values are large integers (> 100), treat as DN
    if np.median(dst_array[valid_mask]) > 50.0:
        # Approximate scaling factor
        dst_array = (dst_array ** 2) / 10000.0

    if output_tif_path:
        output_tif_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(
            output_tif_path,
            "w",
            driver="GTiff",
            height=grid.height,
            width=grid.width,
            count=1,
            dtype=np.float32,
            crs=grid.crs,
            transform=dst_transform,
            nodata=0.0
        ) as dst:
            dst.write(dst_array, 1)

    return dst_array, valid_mask
