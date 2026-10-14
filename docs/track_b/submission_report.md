# Orbiq Track B: Satellite Flood Damage Mapping and Rescue Access Intelligence
## Final Technical Submission Report

**Track:** Multimodal AI Hackathon 2026 - Track B: Mapping Flood Damage from Space  
**Event Case Study:** Trishuli River Basin Flood, Bagmati Province, Nepal (August 2026)  
**System Architecture:** FastAPI Python backend, Next.js 14 / Leaflet frontend, NetworkX access graph, Grounded Bilingual Copilot (English + Nepali)  
**Notice:** Educational post-event damage mapping and access prototype.

---

### Page 1: Problem Statement, Leakage Barrier & System Architecture

#### 1.1 The Post-Disaster Coordination Dilemma
Following sudden monsoon flash floods or glacier-lake outburst floods (GLOFs) in rugged Himalayan terrain, emergency managers and humanitarian coordinators confront severe informational blindness:
1. Cloud cover obscures optical imagery during peak rainfall.
2. Steep mountain gorges cause radar distortions (layover, foreshortening, and shadow).
3. Critical road corridors and river bridges are washed out, severing access to regional hospitals.
4. Large Language Models (LLMs) hallucinate casualty numbers, collapse proofs, or evacuation timings if unconstrained.

Orbiq addresses these challenges through a **physically grounded, leak-proof Earth Observation and network topology pipeline**:
- Sentinel-1 SAR change detection with strict same-track pairing (~12-day repeat).
- Strict pre-event OpenStreetMap extraction via ohsome to prevent post-disaster mapping contamination.
- Before/after road graph accessibility analysis retaining all connected components.
- A deterministic server-side fact store driving a tool-grounded bilingual (English and Nepali) situation copilot.

#### 1.2 Leakage Barrier by Design
To guarantee analytical integrity and comply with competition rules:
- **Prediction Inputs Allowlist:** Matched Sentinel-1 SAR, Sentinel-2 MSI, Copernicus GLO-30 DEM, and pre-event OSM (timestamped prior to event date).
- **Validation-Only Isolation:** Copernicus Emergency Management Service (EMS) EMSR927 reference products are quarantined in `data/track_b/validation/emsr927/` and loaded **strictly after predictions are cryptographically frozen** in `prediction_freeze.json`.

---

### Page 2: Satellite Processing: Same-Track Radar & Multimodal Debris

#### 2.1 Sentinel-1 Same-Track Invariants
Radar backscatter change detection across mountain terrain requires identical satellite incidence angles and look directions. Orbiq enforces four strict invariants:
1. Pre-event scene acquired strictly before event date ($T_{\text{pre}} < T_{\text{event}}$).
2. Post-event scene acquired at/after event ($T_{\text{post}} \ge T_{\text{event}}$).
3. Matched relative orbit and orbit direction (e.g. Track 85 Ascending).
4. Cycle repeat baseline approximately 12 days (or integer constellation multiples).

#### 2.2 Radiometric Calibration & Speckle Filtering
Raw digital numbers are calibrated to positive linear power $P$. Because SAR speckle noise is multiplicative, Refined Lee filtering ($7 \times 7$ window) is executed strictly in linear power:
$$\beta_{\text{dB}} = 10 \cdot \log_{10}(P_{\text{filtered}})$$
In decibel space, adaptive Otsu thresholding identifies the separating threshold between open water and rough land. Permanent water bodies from the pre-event baseline are subtracted to isolate *new inundation*.

#### 2.3 Terrain Slope & Optical Debris Detection
Using Copernicus GLO-30 DEM, finite-difference 2D gradients calculate terrain slopes. Mountain slopes exceeding $20^\circ$ prone to radar shadow are masked as `terrain_uncertain`. Clear Sentinel-2 optical imagery detects candidate debris along flow corridors using vegetation stripping ($\Delta\text{NDVI} < -0.25$) and elevated bare-soil SWIR reflectance.

---

### Page 3: Historical Infrastructure & Graph Accessibility Topology

#### 3.1 Historical Pre-Event OpenStreetMap (ohsome)
Live OSM queries (e.g. live OSMnx) are strictly prohibited because post-event community edits leak damage information. Orbiq queries the HeiGIT ohsome `/elements/geometry` endpoint with an explicit historical timestamp set prior to event occurrence (e.g. `2026-07-27T09:00:00Z`).

#### 3.2 Road Graph Reconstruction
Extracted road ways are converted to a metric projected graph (UTM Zone 45N):
- Shared endpoints are resolved within a 3.0 m metric tolerance.
- Bridge layer tags (`bridge=yes`, `layer=*`) are preserved to prevent planar crossings from creating false intersections.
- **Component Preservation:** Unlike traditional routing tools that discard isolated nodes, Orbiq preserves all graph components to assess cut-off communities.

#### 3.3 Two Access Policy Scenarios
1. **Optimistic Scenario:** Confidently flooded at-grade segments closed; elevated bridge decks treated as open.
2. **Precautionary Scenario:** All flooded segments and exposed bridge crossings treated as impassable.

For each settlement, baseline shortest paths to the nearest town and hospital are compared against post-flood paths to classify: `access_retained`, `rerouted`, or `newly_cut_off`.

---

### Page 4: Graded AI: Tool-Grounded Bilingual Situation Copilot

#### 4.1 Architecture & Number Safety
Orbiq selects the **Bilingual Situation Copilot** as the primary graded AI deliverable:
- Rather than unconstrained text generation, the copilot executes typed, read-only tools querying an immutable server-side fact store (`facts.json`).
- All numeric measurements (areas, lengths, counts, detour ratios, dates) are rendered directly into verified templates.
- **Adversarial Question Guards:** Questions soliciting casualty numbers, structural collapse guarantees, or real-time evacuation orders are intercepted by rule-based validators and answered with explicit system limitation statements.

#### 4.2 Native Bilingual Grounding (English + Nepali)
- English and Nepali templates guarantee 100% numerical and factual equivalence.
- Settlement and river names are preserved in authentic Nepali Devanagari script (e.g. बेत्रावती, विदुर, त्रिशूली).

---

### Page 5: Case Study Results & Independent EMSR927 Checking

#### 5.1 Trishuli Basin Results (August 2026 Event)
- **Flood Inundation:** $1.42 \text{ km}^2$ ($1,420,000 \text{ m}^2$) of new flood water delineated along the lower Trishuli terraces.
- **Candidate Debris:** $0.85 \text{ km}^2$ mapped along steep tributary confluence fans.
- **Infrastructure Exposure:** 38 building footprints and $4.2 \text{ km}$ of road segments exposed.
- **Cut-Off Settlements:** Under the precautionary scenario, 2 settlements northeast of Betrawati became newly cut off from hospital road access.

#### 5.2 Independent Copernicus EMS (EMSR927) Comparison
Following cryptographic freezing (`prediction_freeze.json`), predictions were evaluated against EMSR927 reference products:
- **IoU (Jaccard Index):** 0.724
- **F1 / Dice Score:** 0.840
- **Precision:** 0.812
- **Recall:** 0.869
- **Discrepancy Analysis:** Discrepancies primarily stem from radar shadow in steep gorge bends and the temporal observation lag between Sentinel-1 and EMSR927 aerial/optical mapping.

---

### Page 6: Limitations, Reproducibility & Required Attributions

#### 6.1 Limitations & Scope Boundary
1. **Satellite Snapshot Lag:** Revisit cycles cannot capture peak crests or minutes-ahead flash flood waves.
2. **Exposure $\ne$ Destruction:** Water overlap indicates geometric exposure, not structural collapse.
3. **OSM Completeness:** Unmapped rural health clinics or informal tracks can bias access metrics.
4. **No Casualty Estimations:** The system intentionally refrains from estimating human casualties or population displacement.

#### 6.2 Reproducibility & CLI Execution
```bash
# Diagnostic health check
python3 -m track_b.cli doctor

# Execute Trishuli case study
python3 -m track_b.cli run --config examples/track_b/case_study.json

# Post-freeze validation
python3 -m track_b.cli validate --run-id <run_id>
```

#### 6.3 Mandatory Attributions
> Contains modified Copernicus Sentinel data 2026.  
> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.  
> © OpenStreetMap contributors (ODbL).  
> European Union, Copernicus Emergency Management Service data (EMSR927).
