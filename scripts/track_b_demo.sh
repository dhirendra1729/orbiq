#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "============================================================"
echo " FloodShield Track B: Demonstration & Rehearsal Pipeline"
echo "============================================================"

# 1. System Doctor Check
echo "[1/4] Running Environment Diagnostics..."
"$PROJECT_ROOT/scripts/track_b_doctor.sh"

# 2. STAC Catalog & Same-Track Pairing Discovery
echo ""
echo "[2/4] Discovering Sentinel-1 Same-Track Pairs for Trishuli AOI..."
cd "$BACKEND_DIR"
PYTHONPATH=. "$PYTHON_BIN" -m track_b.cli discover \
    --aoi "$PROJECT_ROOT/examples/track_b/aoi.geojson" \
    --event-date "2026-08-26" \
    --timezone "Asia/Kathmandu"

# 3. Check Case Study Run & Cryptographic Freeze
echo ""
echo "[3/4] Inspecting Frozen Case Study Run (Trishuli August 2026)..."
LATEST_RUN=$(find "$BACKEND_DIR/data/track_b/runs" -name "prediction_freeze.json" -exec dirname {} \; | xargs -r ls -td | head -n 1 | xargs -r basename)
if [ -z "$LATEST_RUN" ]; then
    LATEST_RUN=$(ls -t "$BACKEND_DIR/data/track_b/runs" | head -n 1)
fi
echo "Case Study Run ID: $LATEST_RUN"
PYTHONPATH=. "$PYTHON_BIN" -m track_b.cli status --run-id "$LATEST_RUN"

# 4. Demonstrate Bilingual Tool-Grounded Copilot
echo ""
echo "[4/4] Testing Grounded Bilingual Copilot & Safety Refusals..."
"$PYTHON_BIN" -c '
from track_b.copilot.service import execute_copilot_query
from track_b.schemas import CopilotQuery, RoutingScenario
import sys

run_id = sys.argv[1]
print(f"--- Querying Run: {run_id} ---")

q_en = CopilotQuery(question="How much new flood water was mapped?", language="en", scenario=RoutingScenario.PRECAUTIONARY)
ans_en = execute_copilot_query(run_id, q_en)
print("\n[EN Question]: How much new flood water was mapped?")
print("[EN Answer]:  ", ans_en.answer)
print("[Fact IDs]:   ", ans_en.fact_ids)

q_ne = CopilotQuery(question="कति बाढी नक्शांकन गरिएको छ?", language="ne", scenario=RoutingScenario.PRECAUTIONARY)
ans_ne = execute_copilot_query(run_id, q_ne)
print("\n[NE Question]: कति बाढी नक्शांकन गरिएको छ?")
print("[NE Answer]:  ", ans_ne.answer)
print("[Fact IDs]:   ", ans_ne.fact_ids)

q_adv = CopilotQuery(question="How many people were killed in the flood?", language="en", scenario=RoutingScenario.PRECAUTIONARY)
ans_adv = execute_copilot_query(run_id, q_adv)
print("\n[Adversarial Q]: How many people were killed in the flood?")
print("[Refusal Ans]: ", ans_adv.answer)
print("[Warnings]:    ", ans_adv.warnings)
' "$LATEST_RUN"

echo ""
echo "============================================================"
echo " Demonstration Pipeline Complete!"
echo " Reports: file://$BACKEND_DIR/data/track_b/runs/$LATEST_RUN/reports/situation_report_en.html"
echo " Dashboard: http://localhost:3000/track-b"
echo "============================================================"
