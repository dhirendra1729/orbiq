# Track B: Data Sources, Attributions & Usage Terms

## 1. Input Allowlist for Prediction

| Dataset / Service | Role in Track B | API / Endpoint / Source | License & Terms | Exact Attribution Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Copernicus Sentinel-1 SAR** | Primary flood radar evidence (VV/VH, IW mode, same relative orbit, ~12-day pair) | CDSE STAC (`https://stac.dataspace.copernicus.eu/v1/`) / AWS Element84 STAC (`https://earth-search.aws.element84.com/v1`) | Open Copernicus Data Access Policy | `Contains modified Copernicus Sentinel data 2026.` |
| **Copernicus Sentinel-2 MSI** | Multispectral optical confirmation & candidate debris detection (L2A bottom-of-atmosphere bands, SCL scene classification) | CDSE STAC / AWS Earth Search | Open Copernicus Data Access Policy | `Contains modified Copernicus Sentinel data 2026.` |
| **Copernicus GLO-30 DEM** | Terrain slope masking, radar orthorectification/topographic correction, downstream flow path bonus | AWS Open Data (`s3://copernicus-dem-30m/`) / Public HTTPS tile mirror | Copernicus WorldDEM-30 terms | `Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.` |
| **Historical OpenStreetMap (via ohsome)** | Pre-event road network, building footprints, bridges, settlements, and hospital infrastructure | HeiGIT ohsome API (`https://api.ohsome.org/v1/elements/geometry`) with strict historical timestamp | Open Database License (ODbL) 1.0 | `© OpenStreetMap contributors.` |

---

## 2. Checking-Only & Reference Datasets (Strictly Post-Freeze)

| Dataset | Role | Source | Separation Rule |
| :--- | :--- | :--- | :--- |
| **Copernicus EMS EMSR927** | Trishuli flood post-event delineation and grading reference | `https://mapping.emergency.copernicus.eu/activations/EMSR927/` and HDX (`https://data.humdata.org/dataset/npl-flood-emsr927`) | **Checking only**. Never used as inference input, training label, or threshold tuning. Loaded only after `prediction_freeze.json` is generated. |

---

## 3. Optional Offline Training Datasets (Segmentation Lane)

| Dataset | Paper / Source | License Notes |
| :--- | :--- | :--- |
| **Kuro Siwo** | Bountos et al., NeurIPS 2024 Datasets and Benchmarks | Repository code: MIT; Dataset: CC BY 4.0. Must cite official paper. |
| **Sen1Floods11** | Bonafilia et al., CVPRW 2020 | Public data, check mirror licensing prior to any model weight training. |
