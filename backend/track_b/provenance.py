"""Input allowlist enforcement, cryptographic manifest generation, and prediction freeze."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from track_b.config import settings
from track_b.schemas import RunStatus
from track_b.store import get_run_dir, save_run_status, atomic_write


ALLOWED_PREDICTION_INPUTS = {
    "sentinel_1_sar": "Copernicus Sentinel-1 SAR (IW mode, VV/VH, same relative orbit)",
    "sentinel_2_opt": "Copernicus Sentinel-2 MSI (L2A bottom-of-atmosphere reflectance)",
    "copernicus_dem": "Copernicus GLO-30 Digital Elevation Model",
    "historical_osm": "Historical OpenStreetMap via ohsome API strictly prior to event timestamp",
}

CHECKING_ONLY_DATASETS = {
    "emsr927": "Copernicus Emergency Management Service EMSR927 rapid mapping products",
    "unosat": "UNOSAT preliminary satellite damage assessment maps",
}

FORBIDDEN_PREDICTION_INPUTS = {
    "live_osm": "Live or post-event OpenStreetMap edits / OSMnx live queries",
    "published_damage_maps": "Copernicus EMS, UNOSAT, or any post-disaster manual damage vector layers",
    "weather_news": "Open-Meteo weather or news feeds as prediction inputs",
}


def get_git_revision() -> str:
    """Read the current git commit revision cleanly."""
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(settings.backend_root),
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return rev
    except Exception:
        return "git_revision_unavailable"


def hash_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_no_reference_leakage(inputs_dir: Path):
    """Enforce that no checking-only reference files (EMS, UNOSAT) are present in the inputs directory."""
    for p in inputs_dir.rglob("*"):
        if p.is_file():
            lower_name = p.name.lower()
            if any(term in lower_name for term in ("emsr", "copernicus_ems", "unosat", "damage_grade", "grading")):
                raise ValueError(
                    f"LEAKAGE DETECTED: Reference product '{p.name}' found in inputs directory {inputs_dir}. "
                    "Copernicus EMS / UNOSAT data is strictly checking-only and forbidden during prediction."
                )


def freeze_prediction_run(run_id: str, status: RunStatus) -> Dict[str, Any]:
    """Cryptographically freeze prediction outputs before any validation is performed."""
    run_dir = get_run_dir(run_id)
    inputs_dir = run_dir / "inputs"
    derived_dir = run_dir / "derived"

    verify_no_reference_leakage(inputs_dir)

    derived_hashes: Dict[str, str] = {}
    if derived_dir.exists():
        for file_path in sorted(derived_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(run_dir).as_posix()
                derived_hashes[rel_path] = hash_file(file_path)

    git_rev = get_git_revision()
    now = datetime.now(timezone.utc).isoformat()
    config_dict = status.request.model_dump()
    config_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode("utf-8")).hexdigest()

    freeze_payload = {
        "run_id": run_id,
        "frozen_at": now,
        "code_git_revision": git_rev,
        "config_sha256": config_hash,
        "derived_file_hashes": derived_hashes,
        "status": "FROZEN_FOR_INDEPENDENT_CHECKING",
        "allowed_inputs_declared": ALLOWED_PREDICTION_INPUTS,
        "notice": "Predictions in this run are locked. No validation reference data has entered inference."
    }

    freeze_hash = hashlib.sha256(json.dumps(freeze_payload, sort_keys=True).encode("utf-8")).hexdigest()
    freeze_payload["freeze_hash"] = freeze_hash

    freeze_file = run_dir / "prediction_freeze.json"
    atomic_write(freeze_file, freeze_payload)

    status.prediction_frozen = True
    status.freeze_hash = freeze_hash
    save_run_status(status)

    return freeze_payload
