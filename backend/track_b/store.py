"""Durable atomic store and SQLite index for Track B runs and artifacts."""

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from track_b.config import settings
from track_b.schemas import JobStage, RunStatus, TrackBRequest, StageProgress


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db():
    """Initialize the SQLite run metadata database."""
    db_path = settings.sqlite_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                event_date TEXT NOT NULL,
                aoi_hash TEXT NOT NULL,
                prediction_frozen INTEGER NOT NULL DEFAULT 0,
                freeze_hash TEXT
            )
        """)
        conn.commit()


init_db()


def atomic_write(target_path: Path, content: Union[str, bytes, dict]):
    """Atomically write content to target_path using a temporary sibling file."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + f".tmp.{uuid.uuid4().hex[:8]}")
    
    if isinstance(content, dict) or isinstance(content, list):
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    elif isinstance(content, str):
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif isinstance(content, bytes):
        with open(temp_path, "wb") as f:
            f.write(content)
    else:
        raise TypeError(f"Unsupported content type: {type(content)}")
    
    temp_path.replace(target_path)


def compute_aoi_hash(aoi_geom: Dict[str, Any]) -> str:
    serialized = json.dumps(aoi_geom, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def get_run_dir(run_id: str) -> Path:
    return settings.runs_dir / run_id


def create_run(req: TrackBRequest) -> RunStatus:
    """Create a new durable run directory and database record."""
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_dir = get_run_dir(run_id)
    (run_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "derived").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    aoi_dict = req.aoi.model_dump()
    aoi_hash = compute_aoi_hash(aoi_dict)
    atomic_write(run_dir / "inputs" / "aoi.geojson", {"type": "Feature", "geometry": aoi_dict, "properties": {}})
    atomic_write(run_dir / "request.json", req.model_dump())

    now = _utcnow_iso()
    initial_stages = {
        stage.value: StageProgress(stage=stage, status="pending").model_dump()
        for stage in JobStage
        if stage not in (JobStage.COMPLETED, JobStage.PARTIAL, JobStage.FAILED, JobStage.CANCELLED)
    }
    initial_stages[JobStage.QUEUED.value]["status"] = "completed"
    initial_stages[JobStage.QUEUED.value]["completed_at"] = now

    status = RunStatus(
        run_id=run_id,
        current_stage=JobStage.QUEUED,
        status="queued",
        request=req,
        stages=initial_stages,
        created_at=now,
        updated_at=now,
        evidence_coverage={},
        prediction_frozen=False,
    )
    save_run_status(status)

    with sqlite3.connect(settings.sqlite_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO runs (run_id, status, current_stage, created_at, updated_at, event_date, aoi_hash, prediction_frozen)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (run_id, status.status, status.current_stage.value, now, now, req.event_date, aoi_hash))
        conn.commit()

    return status


def save_run_status(status: RunStatus):
    """Save run status atomically to disk and update SQLite index."""
    run_dir = get_run_dir(status.run_id)
    status.updated_at = _utcnow_iso()
    atomic_write(run_dir / "status.json", status.model_dump())

    with sqlite3.connect(settings.sqlite_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runs
            SET status = ?, current_stage = ?, updated_at = ?, completed_at = ?, prediction_frozen = ?, freeze_hash = ?
            WHERE run_id = ?
        """, (
            status.status,
            status.current_stage.value,
            status.updated_at,
            status.completed_at,
            1 if status.prediction_frozen else 0,
            status.freeze_hash,
            status.run_id,
        ))
        conn.commit()


def get_run_status(run_id: str) -> Optional[RunStatus]:
    status_file = get_run_dir(run_id) / "status.json"
    if not status_file.exists():
        return None
    try:
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RunStatus.model_validate(data)
    except Exception as exc:
        print(f"Error loading run status for {run_id}: {exc}")
        return None


def list_runs(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent runs from SQLite index."""
    with sqlite3.connect(settings.sqlite_db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT run_id, status, current_stage, created_at, updated_at, completed_at, event_date, aoi_hash, prediction_frozen, freeze_hash
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_artifact(run_id: str, category: str, filename: str, content: Union[str, bytes, dict]) -> Path:
    """Save an artifact file into inputs/, derived/, or reports/."""
    run_dir = get_run_dir(run_id)
    if category not in ("inputs", "derived", "reports"):
        raise ValueError(f"Invalid artifact category: {category}")
    target_path = run_dir / category / filename
    atomic_write(target_path, content)
    return target_path


def get_artifact_path(run_id: str, category: str, filename: str) -> Optional[Path]:
    run_dir = get_run_dir(run_id)
    target_path = (run_dir / category / filename).resolve()
    # Check directory traversal
    try:
        target_path.relative_to(run_dir)
    except ValueError:
        return None
    if target_path.exists():
        return target_path
    return None
