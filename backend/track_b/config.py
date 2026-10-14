"""Configuration settings, capability probes and baseline constants for Orbiq Track B."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings


class TrackBSettings(BaseSettings):
    """Runtime configuration for Track B pipeline."""
    # Base paths
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    backend_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "data" / "track_b"
    runs_dir: Path = Path(__file__).resolve().parent.parent / "data" / "track_b" / "runs"
    cache_dir: Path = Path(__file__).resolve().parent.parent / "data" / "track_b" / "cache"
    validation_dir: Path = Path(__file__).resolve().parent.parent / "data" / "track_b" / "validation"
    sqlite_db_path: Path = Path(__file__).resolve().parent.parent / "data" / "track_b" / "jobs.db"

    # STAC Providers
    earth_search_stac_url: str = "https://earth-search.aws.element84.com/v1"
    cdse_stac_url: str = "https://stac.dataspace.copernicus.eu/v1/"
    stac_timeout_sec: float = 30.0

    # Historical OpenStreetMap (ohsome)
    ohsome_api_base: str = "https://api.ohsome.org/v1"
    ohsome_geometry_url: str = "https://api.ohsome.org/v1/elements/geometry"
    ohsome_metadata_url: str = "https://api.ohsome.org/v1/metadata"
    ohsome_timeout_sec: float = 45.0

    # Copernicus DEM
    dem_cache_dir: Path = Path(__file__).resolve().parent.parent / "data" / "dem"
    dem_aws_base: str = "https://copernicus-dem-30m.s3.amazonaws.com"

    # Processing & Algorithm Defaults
    default_resolution_m: float = 20.0
    max_aoi_sq_km: float = 30000.0
    pair_interval_days: int = 12
    pair_tolerance_days: int = 4
    slope_uncertainty_deg: float = 20.0
    lee_filter_window: int = 7
    mndwi_water_threshold: float = 0.0
    debris_delta_ndvi_threshold: float = -0.25
    debris_swir_threshold: float = 0.15
    graph_context_buffer_m: float = 15000.0
    settlement_snap_distance_m: float = 1000.0

    # AI Copilot Settings
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3"
    copilot_strict_citations: bool = True

    model_config = {
        "env_prefix": "TRACK_B_",
        "extra": "ignore"
    }


def get_settings() -> TrackBSettings:
    settings = TrackBSettings()
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.validation_dir.mkdir(parents=True, exist_ok=True)
    settings.dem_cache_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
