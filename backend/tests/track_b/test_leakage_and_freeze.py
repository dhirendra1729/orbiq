"""Tests for cryptographic freeze and leakage prevention barrier."""

from pathlib import Path
import pytest

from track_b.provenance import verify_no_reference_leakage, freeze_prediction_run
from track_b.schemas import TrackBRequest, RunStatus, JobStage
from track_b.store import create_run
from track_b.validation.emsr927 import compare_with_emsr927


def test_leakage_barrier_detects_reference_files(tmp_path):
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()

    # Place allowed file
    (inputs_dir / "aoi.geojson").write_text("{}", encoding="utf-8")
    verify_no_reference_leakage(inputs_dir)

    # Place forbidden reference product
    (inputs_dir / "EMSR927_AOI01_DEL_PRODUCT_grading.geojson").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
        verify_no_reference_leakage(inputs_dir)


def test_validation_fails_if_prediction_not_frozen(tmp_path):
    # If run has not been frozen, validation must raise error
    req = TrackBRequest(
        aoi={"type": "Polygon", "coordinates": [[[85.1, 27.9], [85.2, 27.9], [85.2, 28.0], [85.1, 28.0], [85.1, 27.9]]]},
        event_date="2026-08-26"
    )
    status = create_run(req)
    assert status.prediction_frozen is False

    with pytest.raises(ValueError, match="have not been frozen"):
        compare_with_emsr927(status.run_id)
