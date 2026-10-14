# Track B 3-Minute Video Demonstration Script (180 Seconds)

**Target Duration:** Exactly 180 seconds (3:00)  
**Presenter Tone:** Grounded, technical, precise, transparent. No hyperbolic marketing claims.

---

## Storyboard & Timing Ledger

### Segment 1: Introduction & Problem Scope (0:00 – 0:20 | 20s)
- **Visual:** FloodShield Track B Dashboard loaded on browser (`http://localhost:3000/track-b`). Top disclaimer banner visible: *Educational prototype — post-event assessment only*.
- **Voiceover:**
  > "Welcome to FloodShield Track B: Satellite Flood Damage Mapping and Rescue Access Intelligence.
  > Following sudden Himalayan monsoon flash floods, rescue coordinators face immediate uncertainty: where is the flood water, what roads or bridges are cut off, and which remote villages have lost access to hospitals?
  > We built an educational post-event assessment system that pairs real satellite radar and optical imagery with historical OpenStreetMap to answer these questions."

---

### Segment 2: Strict Pre-Event Baselines & Same-Track Pairing (0:20 – 0:50 | 30s)
- **Visual:** Click "Load Trishuli Preset" (August 26, 2026, Nuwakot District, Nepal). Form loads coordinates and parameters. Click "Execute Analysis Run". Pipeline stage indicator animates through `discovering`, `acquiring`, `preprocessing`.
- **Voiceover:**
  > "To avoid post-disaster data leakage, historical OpenStreetMap infrastructure is extracted via the ohsome API strictly prior to the event date.
  > For synthetic aperture radar, we enforce strict same-track pairing: Sentinel-1 pass 85 ascending from August 14th as the pre-event reference and August 26th as the post-event observation. Same viewing angle, same orbit direction, exactly 12 days apart.
  > Radar speckle is filtered in linear power using a 7x7 Refined Lee filter before decibel conversion and adaptive Otsu thresholding."

---

### Segment 3: Multimodal Inundation, Slope Masking & Debris (0:50 – 1:20 | 30s)
- **Visual:** Map renders results. Zoom into Trishuli gorge. Toggle layers: blue flood inundation, amber candidate debris, red exposed roads, building footprints. Click a building to open the Feature Evidence Inspector.
- **Voiceover:**
  > "In steep mountain valleys, radar shadows can mimic dark water. Using a Copernicus GLO-30 DEM mosaic, slopes greater than 20 degrees are flagged as terrain-uncertain rather than falsely classified as flood.
  > Pre-event baseline water is subtracted to reveal only newly inundated flood extent.
  > Along drainage corridors, Sentinel-2 optical imagery detects candidate debris flows by identifying sharp vegetation loss paired with high bare-soil reflectance. Clicking any feature displays raw overlap, sensor source, and confidence."

---

### Segment 4: Road Topology & Cut-Off Settlement Routing (1:20 – 1:50 | 30s)
- **Visual:** Switch to "Cut-off Access" tab. Click on a settlement (e.g. Betrawati). Table highlights status. Show map routes to Trishuli District Hospital.
- **Voiceover:**
  > "Flood intersection alone does not prove destruction. We evaluate accessibility under two declared policies: optimistic and precautionary.
  > Graph topology preserves all disconnected components. Rather than simple straight-line distance, we compute shortest network paths to the nearest mapped hospital before and after the flood.
  > Settlements losing their road connection are classified as newly cut off; others requiring longer detours display exact added travel distances."

---

### Segment 5: Tool-Grounded Bilingual Situation Copilot (1:50 – 2:15 | 25s)
- **Visual:** Switch to "AI Copilot" tab. Select "English". Ask: *"How much new flood water is mapped?"* Answer displays with fact badge. Ask adversarial query: *"How many people died in the flood?"* Red refusal banner triggers. Switch toggle to "नेपाली" and click prompt: *"बाढीले कति क्षेत्र डुबानमा पारेको छ?"*
- **Voiceover:**
  > "Our graded AI component is a grounded bilingual situation copilot. Every number, date, and area is rendered server-side from an immutable fact store, preventing LLM hallucinations.
  > When asked unsupported questions, such as casualty figures or structural destruction guarantees, the copilot explicitly refuses, citing system scope limitations.
  > Switching to Nepali renders the identical verified facts in native Devanagari script."

---

### Segment 6: One-Page Situation Report & Reference Comparison (2:15 – 2:40 | 25s)
- **Visual:** Switch to "EMSR927" tab. Show `FROZEN_FOR_CHECKING` hash. Click "Evaluate Against EMSR927 Reference". Display IoU (Jaccard), F1 score, precision, recall, and sensor discrepancy notes. Click "Situation Report (EN)" to preview the clean one-page HTML report.
- **Voiceover:**
  > "Before loading independent reference data, prediction outputs are cryptographically locked in prediction_freeze.json.
  > We then evaluate against Copernicus EMS activation EMSR927, computing IoU and F1 metrics and detailing radar shadow discrepancies.
  > The one-page situation report compiles these verified facts, inspection priorities, and required attributions for rescue coordinators."

---

### Segment 7: DEM Downstream Corridor Bonus & Credits (2:40 – 3:00 | 20s)
- **Visual:** Click upstream on the map. Violet downstream drainage path traces along the river basin. Footer displays mandatory Copernicus and OpenStreetMap attributions.
- **Voiceover:**
  > "As a bonus, clicking any upstream seed traces the D8 gravitational drainage path along the DEM, listing downstream settlements in order of proximity.
  > FloodShield: verifiable Earth observation, historical infrastructure topology, and honest bilingual AI intelligence from space."
