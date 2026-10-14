# Track B 3-Minute Video Demonstration Checklist

This checklist prepares the operator or automated screen recorder to capture the 180-second presentation video.

---

## 1. Environment & Pre-Flight Checks

- [ ] **FastAPI Backend Active:** Started via `./backend/.venv/bin/python -m uvicorn src.main:app --port 8000`
- [ ] **Next.js Frontend Active:** Started via `npm run dev` in `frontend/` (accessible at `http://localhost:3000/track-b`)
- [ ] **Display Settings:** Browser window sized to standard 1080p (1920x1080) with zoom set to 100%.
- [ ] **Clean State:** Previous local browser test cache cleared or loaded on ready run.
- [ ] **Audio Setup:** Clear voice microphone configured with low ambient noise; speech paced at ~140 words per minute.

---

## 2. Segment-by-Segment Rehearsal Steps

| Timestamp | Screen State / Action | Key Script Cue | Check |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:20** | Show dashboard header, logo, and top amber educational banner. | "FloodShield Track B... educational post-event prototype" | [ ] |
| **0:20 – 0:50** | Click "Load Trishuli Preset". Show S1 same-track pairing and ohsome pre-event cutoff date. | "Sentinel-1 pass 85 ascending... exactly 12 days apart" | [ ] |
| **0:50 – 1:20** | Show damage map with blue flood inundation and amber candidate debris. Click a building to open Feature Inspector. | "Slopes > 20 deg slope-masked... candidate debris via S2 optical" | [ ] |
| **1:20 – 1:50** | Switch to "Cut-off Access" tab. Click Betrawati in the table; show hospital route. | "Shortest network paths to nearest hospital before and after" | [ ] |
| **1:50 – 2:15** | Open "AI Copilot" tab. Ask water question. Ask adversarial casualty question (refused). Toggle to Nepali and ask in Devanagari. | "Every number rendered server-side... refuses casualty guesses" | [ ] |
| **2:15 – 2:40** | Open "EMSR927" tab. Click "Evaluate Against EMSR927". Click "Situation Report (EN)" to show one-page report. | "Prediction locked in prediction_freeze.json... IoU and F1 metrics" | [ ] |
| **2:40 – 3:00** | Click upstream point on map to trace purple D8 drainage path. Pan down to show mandatory attributions. | "D8 gravitational drainage path... verifiable Earth observation" | [ ] |

---

## 3. Post-Recording Quality Verification

- [ ] Duration is strictly under 180 seconds.
- [ ] No personal tokens, API keys, or private filesystem paths exposed.
- [ ] Audio volume is balanced; no clipping or distortion.
- [ ] Text in map tooltips, copilot chat, and tables is legible at 1080p.
- [ ] Mandatory Copernicus and OpenStreetMap credits clearly displayed in footer.
