"""One-page situation report generation in HTML and Markdown (English & Nepali)."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import json

from track_b.schemas import RunStatus
from track_b.copilot.tools import load_facts, get_hazard_area, get_asset_exposure, list_access_loss_settlements


ATTRIBUTION_NOTICES = (
    "<p><em>Contains modified Copernicus Sentinel data 2026.</em></p>\n"
    "<p><em>Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 "
    "provided under COPERNICUS by the European Union and ESA; all rights reserved.</em></p>\n"
    "<p><em>© OpenStreetMap contributors (ODbL).</em></p>"
)


def generate_situation_report_html(
    run_status: RunStatus,
    language: str = "en"
) -> str:
    """Generate a clean, printable single-page HTML situation report."""
    run_id = run_status.run_id
    req = run_status.request
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    water_area = get_hazard_area(run_id, "new_water")
    debris_area = get_hazard_area(run_id, "candidate_debris")
    bldg_exp = get_asset_exposure(run_id, "buildings", "water")
    road_exp = get_asset_exposure(run_id, "roads", "water")
    bridge_exp = get_asset_exposure(run_id, "bridges", "water")
    hosp_access = list_access_loss_settlements(run_id, service="hospital", scenario="precautionary")

    is_ne = (language == "ne")

    title = "बाढी क्षति तथा उद्धार मार्ग अवस्था प्रतिवेदन" if is_ne else "Flood Damage & Rescue Access Situation Report"
    disclaimer = (
        "शैक्षिक प्रोटोटाइप: यो प्रत्यक्ष आपतकालीन उद्धार वा वास्तविक समयको चेतावनी प्रणाली होइन।"
        if is_ne else
        "Educational prototype: Not an operational evacuation or real-time life-safety warning system."
    )

    html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <title>FloodShield - {title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 20px;
      color: #1e293b;
      line-height: 1.4;
      font-size: 13px;
    }}
    .header {{
      border-bottom: 2px solid #0284c7;
      padding-bottom: 8px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .header h1 {{ margin: 0; font-size: 20px; color: #0369a1; }}
    .badge {{ background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; }}
    .card h3 {{ margin: 0 0 6px 0; font-size: 13px; color: #334155; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stat {{ font-size: 22px; font-weight: bold; color: #0f172a; margin: 4px 0; }}
    .subtext {{ font-size: 11px; color: #64748b; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 5px 8px; text-align: left; }}
    th {{ background: #f1f5f9; }}
    .footer {{ margin-top: 15px; border-top: 1px solid #cbd5e1; padding-top: 8px; font-size: 10px; color: #64748b; }}
    .alert {{ background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-size: 11px; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <span class="badge">TRACK B POST-EVENT ASSESSMENT</span>
      <h1>FloodShield: {title}</h1>
      <div class="subtext">Run ID: <code>{run_id}</code> | Event: {req.event_date} ({req.event_timezone}) | Generated: {now_str}</div>
    </div>
  </div>

  <div class="alert">
    <strong>NOTICE:</strong> {disclaimer}
  </div>

  <div class="grid">
    <div class="card">
      <h3>{'नक्सांकित बाढी' if is_ne else 'Flood Inundation'}</h3>
      <div class="stat">{water_area.get('area_sq_km', '0.0')} km²</div>
      <div class="subtext">{'सेन्टिनेल-१ रार परिवर्तन' if is_ne else 'Sentinel-1 SAR change detection'}</div>
    </div>
    <div class="card">
      <h3>{'गेग्रान / पहिरो' if is_ne else 'Candidate Debris'}</h3>
      <div class="stat">{debris_area.get('area_sq_km', '0.0')} km²</div>
      <div class="subtext">{'सेन्टिनेल-२ अप्टिकल' if is_ne else 'Sentinel-2 clear optical corridor'}</div>
    </div>
    <div class="card">
      <h3>{'सम्पर्कविहीन बस्तीहरू' if is_ne else 'Cut-off Settlements'}</h3>
      <div class="stat">{hosp_access.get('total_newly_cut_off', 0)}</div>
      <div class="subtext">{'अस्पताल मार्ग अवरुद्ध' if is_ne else 'Lost road access to nearest hospital'}</div>
    </div>
  </div>

  <div class="card" style="margin-bottom: 12px;">
    <h3>{'पूर्वाधार जोखिम विवरण' if is_ne else 'Infrastructure Exposure Summary'}</h3>
    <table>
      <thead>
        <tr>
          <th>{'पूर्वाधार प्रकार' if is_ne else 'Asset Category'}</th>
          <th>{'जोखिममा परेको संख्या / लम्बाइ' if is_ne else 'Exposed Count / Extent'}</th>
          <th>{'प्रमाण आधार' if is_ne else 'Evidence Basis'}</th>
          <th>{'निरीक्षण प्राथमिकता' if is_ne else 'Inspection Priority'}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{'घर तथा भवनहरू' if is_ne else 'Buildings'}</td>
          <td>{bldg_exp.get('count', 0)} {'वटा' if is_ne else 'structures'}</td>
          <td>{'ओभरल्याप' if is_ne else 'Pre-event OSM footprint overlap'}</td>
          <td>{'मध्यम' if is_ne else 'Medium'}</td>
        </tr>
        <tr>
          <td>{'सडक सञ्जाल' if is_ne else 'Road Network'}</td>
          <td>{round((road_exp.get('count', 0) or 0) / 1000.0, 2)} km</td>
          <td>{'लाइनस्ट्रिङ प्रतिच्छेदन' if is_ne else 'Metric line intersection'}</td>
          <td>{'उच्च' if is_ne else 'High'}</td>
        </tr>
        <tr>
          <td>{'पुलहरू' if is_ne else 'Bridges'}</td>
          <td>{bridge_exp.get('count', 0)} {'वटा' if is_ne else 'bridges'}</td>
          <td>{'जल सतह सम्पर्क' if is_ne else 'Hazard envelope intersection'}</td>
          <td><strong>{'अति उच्च (प्राथमिकता)' if is_ne else 'Urgent (Priority 1)'}</strong></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="footer">
    {ATTRIBUTION_NOTICES}
  </div>
</body>
</html>"""
    return html
