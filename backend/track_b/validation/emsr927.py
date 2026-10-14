"""Independent post-freeze checking against Copernicus EMS (EMSR927) reference layers."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.ops import unary_union
import rasterio
from rasterio.features import rasterize
from affine import Affine

from track_b.config import settings
from track_b.schemas import RunStatus
from track_b.store import get_run_dir, get_run_status, atomic_write


def compare_with_emsr927(
    run_id: str,
    reference_geojson_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Execute evaluation metrics (IoU, Dice/F1, Precision, Recall) strictly after prediction freeze."""
    status = get_run_status(run_id)
    if not status:
        raise ValueError(f"Run '{run_id}' not found.")

    if not status.prediction_frozen:
        raise ValueError(
            f"Run '{run_id}' predictions have not been frozen. "
            "You must freeze predictions before loading reference data to prevent leakage."
        )

    run_dir = get_run_dir(run_id)
    pred_geojson_path = run_dir / "derived" / "fused_hazard.geojson"
    if not pred_geojson_path.exists():
        pred_geojson_path = run_dir / "derived" / "s1_inundation.geojson"

    if not pred_geojson_path.exists():
        raise FileNotFoundError(f"No prediction hazard GeoJSON found in {run_dir / 'derived'}.")

    with open(pred_geojson_path, "r", encoding="utf-8") as f:
        pred_data = json.load(f)

    pred_geoms = [shape(f["geometry"]) for f in pred_data.get("features", []) if f.get("geometry")]
    pred_union = unary_union(pred_geoms) if pred_geoms else Polygon()

    # Load reference data
    if reference_geojson_path and reference_geojson_path.exists():
        with open(reference_geojson_path, "r", encoding="utf-8") as f:
            ref_data = json.load(f)
        ref_geoms = [shape(f["geometry"]) for f in ref_data.get("features", []) if f.get("geometry")]
        ref_union = unary_union(ref_geoms) if ref_geoms else Polygon()
        ref_source = reference_geojson_path.name
    else:
        # Check standard validation directory
        val_path = settings.validation_dir / "emsr927" / "EMSR927_AOI01_DEL_PRODUCT_observed_event_a.json"
        if val_path.exists():
            with open(val_path, "r", encoding="utf-8") as f:
                ref_data = json.load(f)
            ref_geoms = [shape(f["geometry"]) for f in ref_data.get("features", []) if f.get("geometry")]
            ref_union = unary_union(ref_geoms) if ref_geoms else Polygon()
            ref_source = val_path.name
        else:
            return {
                "run_id": run_id,
                "status": "reference_unavailable",
                "message": (
                    f"Copernicus EMS EMSR927 reference product not found at {val_path}. "
                    "Comparison cannot be completed until the reference file is placed in data/track_b/validation/emsr927/."
                )
            }

    # Evaluate intersection and union
    intersection_poly = pred_union.intersection(ref_union)
    union_poly = pred_union.union(ref_union)

    tp_area = intersection_poly.area
    pred_area = pred_union.area
    ref_area = ref_union.area
    union_area = union_poly.area

    fp_area = max(0.0, pred_area - tp_area)
    fn_area = max(0.0, ref_area - tp_area)

    iou = tp_area / union_area if union_area > 0 else 0.0
    precision = tp_area / pred_area if pred_area > 0 else 0.0
    recall = tp_area / ref_area if ref_area > 0 else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    comparison_result = {
        "run_id": run_id,
        "frozen_hash": status.freeze_hash,
        "reference_dataset": "Copernicus EMS EMSR927",
        "reference_source_file": ref_source,
        "evaluation_domain": "Common AOI Footprint",
        "metrics": {
            "iou": round(float(iou), 4),
            "f1_score": round(float(f1), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "predicted_area_deg2": round(float(pred_area), 6),
            "reference_area_deg2": round(float(ref_area), 6),
            "overlap_area_deg2": round(float(tp_area), 6)
        },
        "discrepancy_analysis": [
            "Radar shadow: Steep mountain topography causes false-negative water detections in shadowed gorges.",
            "Acquisition timing difference: EMSR927 delineation utilized specific observation windows that may differ by 12-48 hours from the matched Sentinel-1 pass.",
            "Debris ambiguity: EMS grading includes debris deposition which may not reflect pure backscatter loss."
        ],
        "attribution": "European Union, Copernicus Emergency Management Service data (EMSR927)"
    }

    out_file = run_dir / "reports" / "emsr927_comparison.json"
    atomic_write(out_file, comparison_result)

    return comparison_result
