# Case Study: Trishuli River Basin Flood & Access Loss Intelligence (August 2026)

## 1. Event Overview & Geographic Domain

- **Event Identifier:** Trishuli River Monsoon Flash Flood & Debris Event
- **Event Date:** 2026-08-26 (Nepal Standard Time, `Asia/Kathmandu`)
- **Geographic Area of Interest (AOI):**
  - **Coordinates:** $85.12^\circ \text{E} - 85.28^\circ \text{E}$, $27.92^\circ \text{N} - 28.08^\circ \text{N}$
  - **Region:** Nuwakot District, Bagmati Province, Nepal
  - **Key Settlements:** Bidur (District headquarters), Betrawati, Battar, Trishuli Bazaar
  - **Terrain:** Deep Himalayan river gorge rising from 550 m (valley floor) to over 2,200 m (flanking mountain ridges)

---

## 2. Satellite Evidence & Observation Provenance

| Evidence Layer | Sensor & Platform | Acquisition UTC | Relative Orbit | Mode / Bands | Processing / Units |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pre-Event SAR** | Sentinel-1B / 1A | 2026-08-14 12:18:24Z | Track 85 (Ascending) | IW Dual-Pol (VV/VH) | Linear power -> Refined Lee (7x7) -> dB |
| **Post-Event SAR** | Sentinel-1A | 2026-08-26 12:18:24Z | Track 85 (Ascending) | IW Dual-Pol (VV/VH) | Linear power -> Refined Lee (7x7) -> dB |
| **Pre-Event Optical** | Sentinel-2A MSI | 2026-08-20 05:08:31Z | N/A | L2A (B02, B03, B04, B08, B11, SCL) | Surface reflectance, clear SCL |
| **Post-Event Optical**| Sentinel-2B MSI | 2026-08-28 05:08:19Z | N/A | L2A (B02, B03, B04, B08, B11, SCL) | Surface reflectance, valley corridor |
| **Terrain Elevation** | Copernicus GLO-30 DEM | Tiles `N27E085`, `N28E085` | N/A | 30 m elevation (WGS84 ellipsoidal) | Finite-difference slope gradient |

---

## 3. Historical Infrastructure Baseline (ohsome)

- **Snapshot Invariant:** Extracted strictly prior to event date (effective snapshot `2026-07-27T09:00:00Z` reflecting provider temporal maximum).
- **Extracted Assets:**
  - Highway network: Trishuli Highway (Pasang Lhamu Highway), secondary and residential links
  - Bridges: Critical river crossings at Betrawati and Bidur
  - Health Facilities: Trishuli District Hospital (Bidur), community health posts
  - Settlements: 18 mapped settlements (towns, villages, hamlets)

---

## 4. Derived Assessment Findings

1. **Hazard Inundation Envelope:**
   - Identified new water along the lower valley terrace and alluvial sandbars.
   - Identified candidate debris and sediment deposition where steep side-tributaries enter the main Trishuli channel ($\Delta\text{NDVI} < -0.25$ with elevated SWIR reflectance).
   - Permanent water subtraction prevented baseline river channels from falsely inflating new inundation figures.
2. **Infrastructure Exposure:**
   - At-grade road segments intersecting low terrace inundation flagged as exposed.
   - Critical bridge crossings flagged as high-priority inspection points.
3. **Access Isolation:**
   - Under the precautionary scenario (closing flooded links and exposed bridge approaches), upstream settlements northeast of Betrawati lose primary road access to Trishuli District Hospital.
   - Detour routing estimates extra travel distances for rerouted settlements.
4. **Independent EMSR927 Checking:**
   - Executed strictly post-freeze (`prediction_freeze.json`).
   - Discrepancy analysis identifies mountain radar shadow as the primary source of missed backscatter detections in narrow gorge bends.
