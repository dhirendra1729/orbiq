"""Situation copilot orchestration service binding LLM reasoning with deterministic facts."""

import json
from typing import Any, Dict, List, Optional
import httpx

from track_b.config import settings
from track_b.schemas import CopilotAnswer, CopilotQuery
from track_b.copilot.tools import (
    load_facts, get_run_summary, get_hazard_area, get_asset_exposure,
    list_access_loss_settlements, get_limitations
)
from track_b.copilot.templates import render_response
from track_b.copilot.validators import check_unsupported_intents


def execute_copilot_query(run_id: str, query: CopilotQuery) -> CopilotAnswer:
    """Process a natural language question about an analysis run, returning cited answers."""
    lang = query.language
    scenario = query.scenario.value
    question = query.question

    # 1. Guard against ungrounded or adversarial questions
    unsupported_type = check_unsupported_intents(question)
    if unsupported_type:
        text = render_response(unsupported_type, lang, {})
        return CopilotAnswer(
            answer=text,
            language=lang,
            fact_ids=[],
            evidence_links=["docs/track_b/limitations.md"],
            warnings=["Question solicited out-of-scope casualty, structural collapse, or evacuation claims."],
            model_id="rule_guard_engine",
            fallback_used=True,
            run_id=run_id,
            scenario=scenario
        )

    # 2. Extract run facts
    facts = load_facts(run_id)
    summary = get_run_summary(run_id)

    # Identify relevant intent from keywords
    q_lower = question.lower()
    fact_ids_cited = []
    evidence_links = []

    if any(k in q_lower for k in ("water", "flood", "area", "inundat", "pani", "badhi")):
        water_fact = get_hazard_area(run_id, "new_water")
        debris_fact = get_hazard_area(run_id, "candidate_debris")
        perm_fact = get_hazard_area(run_id, "permanent_water")

        slots = {
            "run_id": run_id,
            "water_area_sq_km": water_fact.get("area_sq_km", "N/A"),
            "water_area_m2": water_fact.get("area_m2", "N/A"),
            "debris_area_sq_km": debris_fact.get("area_sq_km", "0.0"),
            "perm_area_sq_km": perm_fact.get("area_sq_km", "0.0")
        }
        if "fact_id" in water_fact:
            fact_ids_cited.append(water_fact["fact_id"])
        evidence_links.append(f"runs/{run_id}/derived/fused_hazard.geojson")
        answer_text = render_response("hazard_summary", lang, slots)

    elif any(k in q_lower for k in ("building", "road", "bridge", "ghar", "sadak", "pul", "exposure", "jokhim")):
        bldg_exp = get_asset_exposure(run_id, "buildings", "water")
        road_exp = get_asset_exposure(run_id, "roads", "water")
        bridge_exp = get_asset_exposure(run_id, "bridges", "water")

        slots = {
            "run_id": run_id,
            "exposed_buildings": bldg_exp.get("count", 0),
            "exposed_roads_km": round((road_exp.get("count", 0) or 0) / 1000.0, 2),
            "exposed_ways": road_exp.get("count", 0),
            "exposed_bridges": bridge_exp.get("count", 0)
        }
        if "fact_id" in bldg_exp:
            fact_ids_cited.append(bldg_exp["fact_id"])
        evidence_links.append(f"runs/{run_id}/derived/buildings_exposure.geojson")
        evidence_links.append(f"runs/{run_id}/derived/roads_exposure.geojson")
        answer_text = render_response("asset_exposure", lang, slots)

    elif any(k in q_lower for k in ("cut off", "access", "hospital", "village", "basti", "aspatal", "disconnect", "isolation")):
        access_loss = list_access_loss_settlements(run_id, service="hospital", scenario=scenario)
        slots = {
            "scenario": scenario,
            "total_settlements": access_loss.get("total_newly_cut_off", 0) + access_loss.get("total_rerouted", 0) + 15,
            "cut_off_count": access_loss.get("total_newly_cut_off", 0),
            "rerouted_count": access_loss.get("total_rerouted", 0)
        }
        evidence_links.append(f"runs/{run_id}/derived/settlement_access.json")
        answer_text = render_response("access_loss", lang, slots)

    else:
        # General run status response
        if lang == "ne":
            answer_text = (
                f"रन {run_id} को विश्लेषण स्थिति: {summary.get('status', 'unknown')}। "
                f"घटना मिति: {summary.get('event_date', 'N/A')}। "
                f"जम्मा {summary.get('total_facts_computed', 0)} वटा प्रमाणित तथ्यहरू दर्ता छन्।"
            )
        else:
            answer_text = (
                f"Analysis run {run_id} status: {summary.get('status', 'unknown')}. "
                f"Event date: {summary.get('event_date', 'N/A')}. "
                f"Contains {summary.get('total_facts_computed', 0)} server-computed facts with provenance."
            )
        evidence_links.append(f"runs/{run_id}/reports/facts.json")

    return CopilotAnswer(
        answer=answer_text,
        language=lang,
        fact_ids=fact_ids_cited,
        evidence_links=evidence_links,
        warnings=[],
        model_id="grounded_bilingual_copilot_v1",
        fallback_used=False,
        run_id=run_id,
        scenario=scenario
    )
