"""Pydantic schemas and typed data contracts for Orbiq Track B."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class JobStage(str, Enum):
    QUEUED = "queued"
    DISCOVERING = "discovering"
    ACQUIRING = "acquiring"
    PREPROCESSING = "preprocessing"
    MAPPING = "mapping"
    HISTORICAL_ASSETS = "historical_assets"
    EXPOSURE = "exposure"
    ACCESSIBILITY = "accessibility"
    FACTS = "facts"
    REPORTING = "reporting"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RoutingScenario(str, Enum):
    OPTIMISTIC = "optimistic"
    PRECAUTIONARY = "precautionary"


class SettlementAccessStatus(str, Enum):
    ACCESS_RETAINED = "access_retained"
    REROUTED = "rerouted"
    ACCESS_LOST_TO_BASELINE = "access_lost_to_baseline_destination"
    NEWLY_CUT_OFF = "newly_cut_off"
    ALREADY_DISCONNECTED = "already_disconnected"
    UNSNAPPED = "unsnapped"
    DESTINATION_MISSING = "destination_missing"
    BOUNDARY_UNCERTAIN = "boundary_uncertain"
    HAZARD_UNASSESSED = "hazard_unassessed"
    TOPOLOGY_UNCERTAIN = "topology_uncertain"


class AOIGeometry(BaseModel):
    """GeoJSON geometry polygon or multipolygon representation with validation."""
    type: Literal["Polygon", "MultiPolygon"]
    coordinates: List[Any]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, coords: List[Any], info) -> List[Any]:
        if not coords:
            raise ValueError("Coordinates array cannot be empty.")
        
        # Helper to validate a linear ring
        def check_ring(ring: List[Any]):
            if len(ring) < 3:
                raise ValueError(f"Linear ring must contain at least 3 coordinates, got {len(ring)}")
            # Check coordinate format [lon, lat]
            for pt in ring:
                if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                    raise ValueError(f"Coordinate pair must be [lon, lat], got {pt}")
                lon, lat = float(pt[0]), float(pt[1])
                if not (-180.0 <= lon <= 180.0):
                    raise ValueError(f"Longitude {lon} out of range [-180, 180]")
                if not (-90.0 <= lat <= 90.0):
                    raise ValueError(f"Latitude {lat} out of range [-90, 90]")
            # Check closure
            if ring[0][0] != ring[-1][0] or ring[0][1] != ring[-1][1]:
                ring.append(ring[0])

        # Validate based on depth
        if coords and isinstance(coords[0], list):
            if coords[0] and isinstance(coords[0][0], list):
                if coords[0][0] and isinstance(coords[0][0][0], (int, float)):
                    # Polygon: list of rings
                    for r in coords:
                        check_ring(r)
                else:
                    # MultiPolygon: list of polygons
                    for p in coords:
                        for r in p:
                            check_ring(r)

        return coords


class TrackBRequest(BaseModel):
    """Execution request contract for Track B analysis."""
    aoi: AOIGeometry
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    event_timezone: str = Field(default="Asia/Kathmandu", description="Event timezone identifier")
    event_time: Optional[str] = Field(default=None, description="Optional ISO time e.g. 06:00:00")
    pre_search_days: int = Field(default=36, ge=1, le=120)
    post_search_days: int = Field(default=24, ge=1, le=120)
    pair_interval_days: int = Field(default=12, ge=6, le=48)
    analysis_resolution_m: float = Field(default=20.0, ge=10.0, le=100.0)
    osm_snapshot_time: Optional[str] = Field(default=None, description="Pre-event OSM snapshot timestamp")
    routing_mode: str = Field(default="motor_vehicle", description="Routing mode: motor_vehicle, emergency, foot")
    graph_context_buffer_m: float = Field(default=15000.0, ge=1000.0, le=50000.0)
    copilot_enabled: bool = True
    segmentation_enabled: bool = False
    downstream_bonus_enabled: bool = True

    @field_validator("event_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except Exception:
            raise ValueError(f"Invalid event_date '{v}'. Must be YYYY-MM-DD.")
        return v


class SceneMetadata(BaseModel):
    """Provenance metadata for an acquired satellite scene."""
    product_id: str
    collection: str
    acquisition_utc: str
    platform: str
    relative_orbit: Optional[int] = None
    orbit_direction: str  # "ascending" or "descending"
    instrument_mode: str
    polarizations: List[str]
    processing_level: str
    bounding_box: List[float]
    coverage_fraction: float
    asset_urls: Dict[str, str] = Field(default_factory=dict)
    scene_valid: bool = True
    rejection_reason: Optional[str] = None


class ScenePair(BaseModel):
    """A verified matched Sentinel-1 pre/post observation pair."""
    pre_scene: SceneMetadata
    post_scene: SceneMetadata
    relative_orbit: int
    orbit_direction: str
    interval_days: float
    valid: bool = True
    pairing_notes: str = ""


class GridSpec(BaseModel):
    """Geospatial working grid for an analysis run."""
    crs: str
    utm_zone: int
    resolution_m: float
    bounds_projected: Tuple[float, float, float, float]
    bounds_wgs84: Tuple[float, float, float, float]
    width: int
    height: int
    transform: List[float]


class FactItem(BaseModel):
    """Deterministic, immutable unit of factual evidence generated server-side."""
    fact_id: str
    run_id: str
    metric: str
    value: Any
    unit: str
    scope: Dict[str, Any] = Field(default_factory=dict)
    evidence_artifacts: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    method_version: str = "1.0.0"
    coverage: Optional[float] = None
    status: str = "computed"


class StageProgress(BaseModel):
    stage: JobStage
    status: str  # "pending", "running", "completed", "failed", "skipped"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: Optional[float] = None
    message: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)


class RunStatus(BaseModel):
    """Durable state and progress manifest for a run."""
    run_id: str
    current_stage: JobStage
    status: str  # "queued", "running", "completed", "failed", "cancelled"
    request: TrackBRequest
    grid: Optional[GridSpec] = None
    stages: Dict[str, StageProgress] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    evidence_coverage: Dict[str, float] = Field(default_factory=dict)
    prediction_frozen: bool = False
    freeze_hash: Optional[str] = None


class SettlementAccessResult(BaseModel):
    """Access loss analysis output for a single settlement."""
    settlement_id: str
    name: str
    place_type: str
    coordinates: List[float]
    snapped: bool
    snap_distance_m: Optional[float] = None
    nearest_town_baseline: Optional[Dict[str, Any]] = None
    nearest_hospital_baseline: Optional[Dict[str, Any]] = None
    nearest_town_post: Optional[Dict[str, Any]] = None
    nearest_hospital_post: Optional[Dict[str, Any]] = None
    status_town: SettlementAccessStatus
    status_hospital: SettlementAccessStatus
    status_overall: SettlementAccessStatus
    detour_ratio_town: Optional[float] = None
    detour_ratio_hospital: Optional[float] = None
    lost_edges_count: int = 0
    boundary_warning: bool = False


class CopilotQuery(BaseModel):
    question: str
    language: Literal["en", "ne"] = "en"
    scenario: RoutingScenario = RoutingScenario.PRECAUTIONARY
    scope: Dict[str, Any] = Field(default_factory=dict)


class CopilotAnswer(BaseModel):
    answer: str
    language: Literal["en", "ne"]
    fact_ids: List[str]
    evidence_links: List[str]
    warnings: List[str] = Field(default_factory=list)
    model_id: str
    fallback_used: bool = False
    run_id: str
    scenario: str
