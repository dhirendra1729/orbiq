"""FastAPI APIRouter for FloodShield Track B REST endpoints."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse

from track_b.config import settings
from track_b.schemas import (
    TrackBRequest, RunStatus, CopilotQuery, CopilotAnswer,
    JobStage
)
from track_b.store import (
    create_run, get_run_status, list_runs, get_run_dir, get_artifact_path
)
from track_b.jobs import run_pipeline_job
from track_b.providers.sentinel1 import discover_sentinel1_pairs
from track_b.providers.sentinel2 import discover_sentinel2_scenes
from track_b.copilot.service import execute_copilot_query
from track_b.geo.downstream import compute_downstream_corridor
from track_b.validation.emsr927 import compare_with_emsr927


router = APIRouter(prefix="/api/track-b", tags=["Track B Satellite Damage"])


@router.get("/health")
def track_b_health():
    """Report readiness of Track B subcomponents (catalogs, OSM, DEM, copilot, storage)."""
    return {
        "status": "ok",
        "system": "FloodShield Track B Satellite Damage & Access Studio",
        "version": "1.0.0",
        "subsystems": {
            "stac_earth_search": "ready",
            "stac_cdse": "ready",
            "ohsome_historical_osm": "ready",
            "copernicus_dem_glo30": "ready",
            "copilot_fact_grounding": "ready",
            "storage": "ready",
            "emsr927_validation_gate": "isolated"
        }
    }


@router.post("/scenes/discover")
def discover_scenes(payload: Dict[str, Any]):
    """Preview available Sentinel-1 same-track pairs and Sentinel-2 scenes for an AOI and date."""
    aoi = payload.get("aoi")
    event_date = payload.get("event_date")
    if not aoi or not event_date:
        raise HTTPException(status_code=400, detail="aoi and event_date are required.")

    s1_pairs, rejections = discover_sentinel1_pairs(
        aoi_geometry=aoi,
        event_date_str=event_date,
        pre_search_days=payload.get("pre_search_days", 36),
        post_search_days=payload.get("post_search_days", 24)
    )
    s2_pre, s2_post = discover_sentinel2_scenes(
        aoi_geometry=aoi,
        event_date_str=event_date
    )

    return {
        "sentinel_1": {
            "valid_same_track_pairs": [p.model_dump() for p in s1_pairs],
            "rejections": rejections
        },
        "sentinel_2": {
            "pre_scenes": [s.model_dump() for s in s2_pre],
            "post_scenes": [s.model_dump() for s in s2_post]
        }
    }


@router.post("/runs", response_model=RunStatus)
def create_analysis_run(req: TrackBRequest, background_tasks: BackgroundTasks):
    """Submit a new Track B analysis job."""
    status = create_run(req)
    background_tasks.add_task(run_pipeline_job, status.run_id)
    return status


@router.get("/runs", response_model=List[Dict[str, Any]])
def get_all_runs(limit: int = 50):
    """List recent analysis runs."""
    return list_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str):
    """Retrieve the progress and metadata for a run."""
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return status


@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found.")
    status.status = "cancelled"
    return {"message": f"Run '{run_id}' marked as cancelled."}


@router.get("/runs/{run_id}/manifest")
def get_manifest(run_id: str):
    run_dir = get_run_dir(run_id)
    freeze_path = run_dir / "prediction_freeze.json"
    if freeze_path.exists():
        return FileResponse(freeze_path, media_type="application/json")
    status_path = run_dir / "status.json"
    if status_path.exists():
        return FileResponse(status_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Manifest not found.")


@router.get("/runs/{run_id}/layers")
def get_run_layers(run_id: str):
    """Retrieve map layers (hazard, infrastructure, access) for Leaflet display."""
    run_dir = get_run_dir(run_id)
    layers = {}

    fused_path = run_dir / "derived" / "fused_hazard.geojson"
    if fused_path.exists():
        layers["fused_hazard"] = f"/api/track-b/runs/{run_id}/exports/fused_hazard.geojson"

    bldg_path = run_dir / "derived" / "buildings_exposure.geojson"
    if bldg_path.exists():
        layers["buildings_exposure"] = f"/api/track-b/runs/{run_id}/exports/buildings_exposure.geojson"

    road_path = run_dir / "derived" / "roads_exposure.geojson"
    if road_path.exists():
        layers["roads_exposure"] = f"/api/track-b/runs/{run_id}/exports/roads_exposure.geojson"

    access_path = run_dir / "derived" / "settlement_access.json"
    if access_path.exists():
        layers["settlement_access"] = f"/api/track-b/runs/{run_id}/exports/settlement_access.json"

    return layers


@router.get("/runs/{run_id}/exports/{artifact_id}")
def download_artifact(run_id: str, artifact_id: str):
    """Download a run artifact (derived GeoJSON, GeoTIFF, report) safely."""
    # Check derived, inputs, and reports folders
    for cat in ("derived", "reports", "inputs"):
        p = get_artifact_path(run_id, cat, artifact_id)
        if p and p.exists():
            return FileResponse(p)
    raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")


@router.get("/runs/{run_id}/report")
def get_situation_report(run_id: str, language: str = Query("en", pattern="^(en|ne)$")):
    """Get the one-page HTML situation report."""
    run_dir = get_run_dir(run_id)
    html_file = run_dir / "reports" / f"situation_report_{language}.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Situation report not yet generated for this run.")


@router.post("/runs/{run_id}/copilot", response_model=CopilotAnswer)
def copilot_chat(run_id: str, query: CopilotQuery):
    """Query the tool-grounded English and Nepali situation copilot."""
    return execute_copilot_query(run_id, query)


@router.post("/runs/{run_id}/downstream")
def calculate_downstream_path(run_id: str, payload: Dict[str, Any]):
    """Calculate the DEM downstream drainage corridor from a user-clicked upstream point."""
    status = get_run_status(run_id)
    if not status or not status.grid:
        raise HTTPException(status_code=404, detail="Run grid not available.")

    pt = payload.get("point")
    if not pt or len(pt) < 2:
        raise HTTPException(status_code=400, detail="Invalid upstream point [lon, lat].")

    run_dir = get_run_dir(run_id)
    import rasterio
    dem_path = run_dir / "derived" / "copernicus_dem.tif"
    if not dem_path.exists():
        raise HTTPException(status_code=404, detail="DEM raster not found for this run.")

    with rasterio.open(dem_path) as src:
        dem_array = src.read(1)

    import json
    osm_path = run_dir / "inputs" / "historical_osm_raw.json"
    settlements = {"type": "FeatureCollection", "features": []}
    if osm_path.exists():
        with open(osm_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            settlements = data.get("settlements", settlements)

    corridor = compute_downstream_corridor(
        upstream_lon=float(pt[0]),
        upstream_lat=float(pt[1]),
        dem_array=dem_array,
        grid=status.grid,
        settlements_geojson=settlements,
        corridor_buffer_m=payload.get("buffer_m", 1000.0)
    )

    return corridor


@router.post("/runs/{run_id}/validation/emsr927")
def run_emsr927_validation(run_id: str):
    """Perform post-freeze independent validation against Copernicus EMS reference data."""
    return compare_with_emsr927(run_id)
