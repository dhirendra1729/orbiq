"""Typed, deterministic read-only tools querying the immutable run fact store."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from track_b.store import get_run_dir, get_run_status
from track_b.schemas import FactItem


def load_facts(run_id: str) -> Dict[str, FactItem]:
    """Load the immutable fact store generated for a completed run."""
    run_dir = get_run_dir(run_id)
    facts_file = run_dir / "reports" / "facts.json"
    if not facts_file.exists() or facts_file.stat().st_size == 0:
        return {}
    with open(facts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: FactItem.model_validate(v) for k, v in data.items()}


def get_run_summary(run_id: str) -> Dict[str, Any]:
    """Fetch high-level run execution summary and satellite pair information."""
    status = get_run_status(run_id)
    if not status:
        return {"error": f"Run '{run_id}' not found."}
    facts = load_facts(run_id)
    
    return {
        "run_id": run_id,
        "event_date": status.request.event_date,
        "event_timezone": status.request.event_timezone,
        "status": status.status,
        "created_at": status.created_at,
        "completed_at": status.completed_at,
        "total_facts_computed": len(facts),
        "prediction_frozen": status.prediction_frozen
    }


def get_hazard_area(run_id: str, hazard_class: str = "new_water") -> Dict[str, Any]:
    """Retrieve measured geographic area for a specific hazard class."""
    facts = load_facts(run_id)
    metric_key = f"{run_id}:hazard:{hazard_class}:area_m2"
    fact = facts.get(metric_key)
    if not fact:
        return {
            "hazard_class": hazard_class,
            "status": "not_assessed",
            "message": f"Hazard class '{hazard_class}' was not assessed or has no valid observations."
        }
    
    area_sq_km = round(fact.value / 1_000_000.0, 3) if isinstance(fact.value, (int, float)) else None
    return {
        "fact_id": fact.fact_id,
        "hazard_class": hazard_class,
        "area_m2": fact.value,
        "area_sq_km": area_sq_km,
        "unit": fact.unit,
        "evidence_artifacts": fact.evidence_artifacts
    }


def get_asset_exposure(run_id: str, asset_type: str = "buildings", hazard_class: str = "water") -> Dict[str, Any]:
    """Retrieve measured counts and lengths/areas of exposed pre-event infrastructure."""
    facts = load_facts(run_id)
    count_key = f"{run_id}:exposure:{asset_type}:{hazard_class}_count"
    fact = facts.get(count_key)
    if not fact:
        return {
            "asset_type": asset_type,
            "hazard_class": hazard_class,
            "status": "not_assessed",
            "value": None
        }
    
    return {
        "fact_id": fact.fact_id,
        "asset_type": asset_type,
        "hazard_class": hazard_class,
        "count": fact.value,
        "unit": fact.unit,
        "evidence_artifacts": fact.evidence_artifacts
    }


def list_access_loss_settlements(
    run_id: str,
    service: str = "hospital",
    scenario: str = "precautionary",
    limit: int = 20
) -> Dict[str, Any]:
    """List settlements that lost access to designated services under the scenario policy."""
    run_dir = get_run_dir(run_id)
    access_file = run_dir / "derived" / "settlement_access.json"
    if not access_file.exists():
        return {"error": "Settlement access analysis has not been completed for this run."}
    
    with open(access_file, "r", encoding="utf-8") as f:
        access_data = json.load(f)

    all_settlements = access_data.get("settlements", [])
    cut_off = []
    rerouted = []

    for s in all_settlements:
        status_key = f"status_{service}" if f"status_{service}" in s else "status_overall"
        status_val = s.get(status_key)
        if status_val == "newly_cut_off":
            cut_off.append(s)
        elif status_val == "rerouted":
            rerouted.append(s)

    return {
        "run_id": run_id,
        "service_queried": service,
        "scenario": scenario,
        "total_newly_cut_off": len(cut_off),
        "total_rerouted": len(rerouted),
        "cut_off_settlements": cut_off[:limit],
        "rerouted_settlements": rerouted[:limit]
    }


def get_limitations(run_id: str) -> Dict[str, Any]:
    """Return explicit methodological boundaries and physical limitations."""
    return {
        "run_id": run_id,
        "limitations": [
            "Educational post-event prototype: not an operational warning or life-safety evacuation system.",
            "Satellite observations reflect pass snapshots; rapid transient flood waves or recession are not captured in real time.",
            "Building/road intersection indicates physical exposure, not confirmed structural collapse or bridge pier destruction.",
            "Historical OpenStreetMap may have incomplete rural mapping, unmapped health clinics, or outdated road classifications.",
            "No casualty, injured person, or population displacement estimations are generated."
        ]
    }
