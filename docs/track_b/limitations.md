# Track B: System Scope, Physical Assumptions & Operational Limitations

> **CRITICAL NOTICE:** Orbiq Track B is an **educational post-event damage mapping and rescue access intelligence prototype**. It is **not** an operational evacuation, real-time life-safety dispatch, or minutes-ahead disaster warning system.

---

## 1. Remote Sensing & Physical Limitations

1. **Acquisition Lag vs. Event Dynamics:** Sentinel-1 has a 12-day repeat orbit (or 6 days when multi-satellite constellations are active in matching orbits). Satellite passes capture snapshots hours or days after peak inundation, missing transient flash floods, glacier-lake outburst peak crests, or receding waters.
2. **Radar Geometry & Mountain Distortion:** In steep Himalayan terrain (such as the Trishuli River basin), radar foreshortening, layover, and mountain radar shadows can mimic low backscatter or obscure deep river gorges. While slope uncertainty masking is applied, residual geometric distortion remains.
3. **Rough Water, Emergent Vegetation & Urban Double-Bounce:** Wind-induced surface roughness increases backscatter over open water, causing false negatives in simple Otsu backscatter thresholding. Similarly, flooded vegetation and urban structures cause radar corner-reflector double bounce, appearing bright rather than dark.
4. **Permanent Water Subtraction:** Inundation is computed relative to an earlier pre-event reference scene. Seasonal reservoir fluctuations, agricultural irrigation cycles, and baseline river channel migrations can affect change detection.
5. **Candidate Debris Ambiguity:** Post-flood bare earth, landslides, riverbed scour, and agricultural harvesting share spectral signatures with debris flows. Without high-resolution optical stereo elevation or in-situ verification, debris detections remain *unconfirmed candidates*.
6. **Spatial Resolution Limits:** With 20 m SAR/optical analysis grids and 30 m Copernicus DEM, small pedestrian bridges, narrow unpaved trails, and buildings smaller than 400 m² cannot be individually resolved with certainty.

---

## 2. Infrastructure & Graph Topology Limitations

1. **Exposure vs. Physical Destruction:** Spatial intersection of a flood or debris polygon with a building footprint or road segment indicates *exposure*, not structural collapse or bridge pier failure. Elevated bridges over high water may retain structural integrity while still showing water in the plan-view pixel.
2. **Historical OSM Completeness & Age:** Pre-event OSM extracted via ohsome reflects community mapping as of the historical snapshot. Missing rural hamlets, unmapped clinics, or outdated road classifications directly affect accessibility and isolation metrics.
3. **Graph Boundary Truncation:** Analysis occurs within a buffered bounding box around the AOI. Detour routes that travel outside the extracted graph boundary may falsely appear cut off (`boundary_uncertain`).
4. **No Casualty or Population Inference:** Building footprints do not indicate occupancy rates, daytime/nighttime populations, or casualty estimates. The system strictly avoids generating ungrounded human-impact figures.

---

## 3. Bilingual AI Copilot & Model Limitations

1. **Fact-Store Grounding:** The English and Nepali situation copilot queries a deterministic, server-side fact store. It does not possess direct perceptual capabilities beyond registered run facts.
2. **Language Fluency & Translation Nuance:** While Nepali templates and formatting preserve exact numeric metrics and place names in original Devanagari script, automated language generation can exhibit phrasing variances and requires local reviewer validation.
3. **Checking Reference Discrepancies:** Copernicus EMS (EMSR927) products were delineated at specific satellite acquisition times with different spatial resolutions and sensor geometries. Spatial divergence between Orbiq predictions and EMS reference vectors reflects sensor, temporal, and methodological differences, not ground-truth errors.
4. **Downstream Terrain Flow Bonus:** The D8 flow accumulation corridor from an upstream point indicates gravitational drainage terrain paths; it does not model hydrodynamics, sediment transport, breach hydrographs, or flood wave arrival velocities.
