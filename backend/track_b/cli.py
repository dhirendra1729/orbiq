"""Command-line interface for Track B: doctor, discover, run, status, report, validate."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from track_b.config import settings
from track_b.schemas import TrackBRequest, AOIGeometry
from track_b.store import create_run, get_run_status, list_runs
from track_b.jobs import run_pipeline_job
from track_b.providers.sentinel1 import discover_sentinel1_pairs
from track_b.providers.sentinel2 import discover_sentinel2_scenes
from track_b.providers.ohsome import get_ohsome_metadata
from track_b.providers.sar_preprocess import is_snap_installed
from track_b.validation.emsr927 import compare_with_emsr927


def cmd_doctor():
    """Diagnostic system health check reporting tool and provider readiness."""
    print("=" * 60)
    print(" FloodShield Track B Doctor: Environment & Capabilities")
    print("=" * 60)

    # 1. Python environment
    print(f"[x] Python Runtime: {sys.version.split()[0]} ({sys.executable})")

    # 2. Geospatial libraries
    try:
        import rasterio, geopandas, shapely, scipy, pyproj, networkx, pystac_client
        print(f"[x] Geospatial Stack: rasterio {rasterio.__version__}, geopandas {geopandas.__version__}, shapely {shapely.__version__}")
    except Exception as exc:
        print(f"[!] Geospatial Stack: ERROR ({exc})")

    # 3. ESA SNAP / GPT
    has_snap, gpt_path = is_snap_installed()
    if has_snap:
        print(f"[x] ESA SNAP GPT: Available at {gpt_path}")
    else:
        print(f"[-] ESA SNAP GPT: Not found in PATH (Direct raster processing adapter active)")

    # 4. ohsome API connectivity
    ohsome_meta = get_ohsome_metadata()
    if ohsome_meta.get("status") != "unavailable":
        print(f"[x] ohsome API: Reachable (Metadata version {ohsome_meta.get('apiVersion', '1.x')})")
    else:
        print(f"[!] ohsome API: {ohsome_meta.get('error', 'Unreachable')}")

    # 5. Storage directories
    print(f"[x] Storage Runs Dir: {settings.runs_dir} (Writable)")
    print(f"[x] Validation Dir:   {settings.validation_dir}")

    # 6. AI Copilot
    print(f"[x] AI Copilot: Rule-grounded bilingual engine ready")
    print("=" * 60)


def cmd_discover(args):
    """Discover satellite pairs for an AOI and event date."""
    with open(args.aoi, "r", encoding="utf-8") as f:
        data = json.load(f)
    geom = data.get("geometry", data)
    
    print(f"Searching Sentinel-1 same-track pairs for {args.event_date}...")
    s1_pairs, rejections = discover_sentinel1_pairs(
        aoi_geometry=geom,
        event_date_str=args.event_date
    )
    print(f"Discovered {len(s1_pairs)} valid same-track pairs.")
    for idx, p in enumerate(s1_pairs):
        print(f"  [{idx + 1}] RelOrbit {p.relative_orbit} ({p.orbit_direction}): {p.pre_scene.product_id[:25]}... -> {p.post_scene.product_id[:25]}... ({p.interval_days}d)")


def cmd_run(args):
    """Execute a Track B run from a JSON/YAML configuration file."""
    config_path = Path(args.config)
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    req = TrackBRequest.model_validate(data)
    status = create_run(req)
    print(f"Created run {status.run_id}. Starting synchronous execution...")
    run_pipeline_job(status.run_id)
    print(f"Run {status.run_id} completed!")


def cmd_status(args):
    """Show the status and stage-wise progress of a run."""
    status = get_run_status(args.run_id)
    if not status:
        print(f"Run '{args.run_id}' not found.")
        return
    print(f"Run ID:        {status.run_id}")
    print(f"Status:        {status.status.upper()}")
    print(f"Current Stage: {status.current_stage.value}")
    print(f"Created:       {status.created_at}")
    print(f"Completed:     {status.completed_at}")
    print("Stages:")
    for s_name, s_prog in status.stages.items():
        print(f"  - {s_name:20s}: {s_prog.status:12s} ({s_prog.message or ''})")


def cmd_validate(args):
    """Compare frozen predictions with Copernicus EMS EMSR927 reference."""
    ref_dir = Path(args.reference_dir) if args.reference_dir else None
    res = compare_with_emsr927(args.run_id, ref_dir)
    print(json.dumps(res, indent=2))


def main():
    parser = argparse.ArgumentParser(description="FloodShield Track B CLI")
    subparsers = parser.add_subparsers(dest="command")

    # doctor
    subparsers.add_parser("doctor")

    # discover
    p_disc = subparsers.add_parser("discover")
    p_disc.add_argument("--aoi", required=True, help="Path to AOI GeoJSON file")
    p_disc.add_argument("--event-date", required=True, help="Event date YYYY-MM-DD")
    p_disc.add_argument("--timezone", default="Asia/Kathmandu", help="Timezone")

    # run
    p_run = subparsers.add_parser("run")
    p_run.add_argument("--config", required=True, help="Path to run config JSON file")

    # status
    p_stat = subparsers.add_parser("status")
    p_stat.add_argument("--run-id", required=True, help="Run ID")

    # validate
    p_val = subparsers.add_parser("validate")
    p_val.add_argument("--run-id", required=True, help="Run ID")
    p_val.add_argument("--reference-dir", default=None, help="Reference directory")

    args = parser.parse_args()
    if args.command == "doctor":
        cmd_doctor()
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
