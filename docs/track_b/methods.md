# Track B: Technical Methodology & Scientific Pipeline

This document outlines the algorithms, formulas, and processing steps implemented in FloodShield Track B.

---

## 1. SAR Preprocessing & Inundation Mapping

### 1.1 Pair Selection Invariants
Sentinel-1 SAR provides cloud-penetrating synthetic aperture radar observations. Reliable change detection requires:
- **Same relative orbit & pass direction** (ascending or descending) to ensure identical viewing geometry and incidence angles.
- **Matched spatial coverage** across the Area of Interest (AOI).
- **Exact ~12-day temporal baseline** (or constellation repeat interval) between a pre-event baseline image and a post-event observation.
- **Dual-polarization IW mode** (preferring VV backscatter, with VH as secondary cross-polarization support).

### 1.2 Radiometric Calibration & Filtering
1. **Calibration:** Digital numbers are converted to linear radar backscatter power ($P$).
2. **Speckle Filtering:** Applied strictly in *linear power space* using a Refined Lee filter ($7 \times 7$ window) because SAR speckle noise is multiplicative ($I = R \cdot S$). Filtering in logarithmic (dB) space introduces negative radiometric bias.
3. **Decibel Conversion:**
   $$\beta_{dB} = 10 \cdot \log_{10}(P_{\text{filtered}})$$
   In decibel space, backscatter from open water and rough land exhibits a bimodal Gaussian distribution suitable for thresholding.
4. **Adaptive Thresholding:** Otsu's thresholding algorithm calculates optimal threshold $T^*$ maximizing between-class variance:
   $$\sigma_B^2(T) = \omega_0(T)\omega_1(T)[\mu_0(T) - \mu_1(T)]^2$$
   Pixels with $\beta_{dB} < T^*$ are classified as water.
5. **Permanent Water Subtraction & Inundation Isolation:**
   $$\text{Inundation}_{\text{new}} = \text{Water}_{\text{post}} \land \neg \text{Water}_{\text{pre}} \land \text{Mask}_{\text{valid}}$$
6. **Terrain Uncertainty Masking:** Copernicus GLO-30 DEM computes slope angle. Mountain slopes $> 20^\circ$ prone to radar layover, foreshortening, and shadow are flagged as `terrain_uncertain` rather than falsely classified as water.

---

## 2. Optical Corroboration & Candidate Debris Detection

### 2.1 Sentinel-2 Processing
When cloud-free Sentinel-2 L2A imagery is available:
- **Quality Scene Classification (SCL):** Masks out clouds (classes 8, 9, 10), cirrus, and cloud shadows (class 3).
- **Modified Normalized Difference Water Index (MNDWI):**
  $$\text{MNDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{SWIR1}}}{\rho_{\text{Green}} + \rho_{\text{SWIR1}}}$$
- **Normalized Difference Vegetation Index (NDVI):**
  $$\text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}}}$$

### 2.2 Candidate Debris Delineation
Debris flows in mountain valleys exhibit sharp decreases in NDVI (vegetation stripping) paired with increases in bare-soil SWIR reflectance along alluvial river corridors:
$$\Delta\text{NDVI} = \text{NDVI}_{\text{post}} - \text{NDVI}_{\text{pre}} < -0.25$$
$$\text{Candidate Debris} = (\Delta\text{NDVI} < -0.25) \land (\text{SWIR}_{\text{post}} > 0.15) \land \neg \text{Water}_{\text{fused}} \land \text{ValleyCorridor}_{\text{DEM}}$$

---

## 3. Historical Infrastructure & Network Topology

### 3.1 Strict Pre-Event Historical OSM (ohsome)
To avoid data contamination from post-disaster mapping edits:
- Query `https://api.ohsome.org/v1/elements/geometry` with an explicit ISO snapshot timestamp set prior to event occurrence.
- Fetch `highway=*`, `building=*`, `bridge=*`, and `place=city|town|village|hamlet`.
- Identify health infrastructure tagged with `amenity=hospital|clinic`.

### 3.2 Graph Topology Reconstruction
- Convert linear ways to metric projected edges (UTM coordinate system).
- Merge coincident endpoints within a 1.0 m tolerance; preserve layer separation (`bridge=yes`, `tunnel=yes`, `layer=*`).
- Maintain directed multigraph properties (`oneway=yes`, access prohibitions).
- Keep all connected components (never filter to largest component only, as isolated settlements must be assessed).

---

## 4. Exposure & Access Isolation Analysis

### 4.1 Asset Exposure
- **Buildings:** Geometric polygon overlap with flood water or debris candidate polygons. Output includes affected area ($m^2$) and fraction.
- **Roads:** Line-string intersection length ($m$) and exposure fraction.
- **Bridges:** Evaluated under two policy scenarios:
  - *Optimistic:* Confidently flooded at-grade segments closed; elevated bridges assessed as open unless overt overtopping.
  - *Precautionary:* All flooded road segments and exposed bridge crossings treated as impassable.

### 4.2 Cut-Off Settlement Classification
For each mapped settlement node $S$:
1. Compute baseline shortest path in $G_{\text{pre}}$ to nearest town $T_0$ and nearest hospital $H_0$.
2. Compute post-event shortest path in $G_{\text{post}}$ under chosen scenario.
3. Classify status:
   - `access_retained`: Path and destination unchanged.
   - `rerouted`: Destination reachable via alternate route with measured detour length.
   - `newly_cut_off`: No path to any eligible destination exists in the extracted network.
   - `already_disconnected`: Settlement had no baseline path prior to the flood.
   - `boundary_uncertain`: Shortest path reaches boundary of extracted graph context buffer.

---

## 5. Tool-Grounded Bilingual Situation Copilot

- The AI copilot operates strictly through typed, read-only tools querying the immutable run fact store.
- Numeric metrics (areas, lengths, counts, dates, names) are filled into deterministic server-side slots.
- Both English (`en`) and Nepali (`ne`) report generators guarantee numeric equivalence across languages.
- Queries seeking casualty estimates, structural collapse guarantees, or evacuation mandates return explicit scope limitation notices.
