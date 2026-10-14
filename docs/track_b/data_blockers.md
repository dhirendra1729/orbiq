# Track B: Data Access, Capabilities & Blockers Ledger

This ledger records verified external resource availability, network reachability, API status, and any credential requirements as tested on this host.

## 1. Environment & Compute

| Component | Status | Details / Impact | Action / Mitigation |
| :--- | :--- | :--- | :--- |
| **Python 3.11 Runtime** | Ready | Dedicated venv initialized at `backend/.venv` | Core geospatial stack installed in clean venv |
| **Node.js / Next.js** | Ready | v22.23.3, npm 12.2.0 | Frontend dashboard ready for Track B studio integration |
| **GDAL CLI (`gdalinfo`)** | CLI absent | No system `gdalinfo` in PATH; Python bindings/rasterio present | Use rasterio / pyproj / shapely for all geospatial transforms and warps |
| **GPU / CUDA** | Not confirmed | No dedicated GPU assumed | Focus on primary graded AI copilot; segmentation lane provided as isolated runnable pipeline |
| **SNAP / `gpt`** | Optional | ESA SNAP GPT executable not present by default | Provide verified processed adapter and clear instructions for optional local SNAP execution |

## 2. Satellite & Geospatial Providers

| Provider / API | Endpoint | Observed Status | Notes |
| :--- | :--- | :--- | :--- |
| **Earth Search STAC** | `https://earth-search.aws.element84.com/v1` | Accessible | `sentinel-1-grd` available; S1 RTC collection absent at runtime. Needs verified calibration handling. |
| **CDSE STAC** | `https://stac.dataspace.copernicus.eu/v1/` | Verification needed | Used for Sentinel-1 & Sentinel-2 scene discovery. |
| **Copernicus DEM (GLO-30)** | AWS Open Data / HTTP | Accessible | Existing tile resolver in `backend/hydro/dem.py` can be extended for multi-tile mosaics. |
| **ohsome API** | `https://api.ohsome.org/v1/metadata` | Tested in specification | Reported temporal max `2026-07-27T09:00Z`. Strict pre-event cutoff required. |
| **Copernicus EMS EMSR927** | HDX / Copernicus Portal | Checking-only | Used strictly for validation post-prediction freeze. |
