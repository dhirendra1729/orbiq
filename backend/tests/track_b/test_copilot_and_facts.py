"""Tests for tool-grounded bilingual situation copilot and fact store."""

import pytest

from track_b.schemas import CopilotQuery, RoutingScenario, FactItem
from track_b.copilot.validators import check_unsupported_intents, validate_numeric_claims
from track_b.copilot.templates import render_response
from track_b.copilot.service import execute_copilot_query


def test_adversarial_casualty_rejected():
    assert check_unsupported_intents("How many people died in the flood?") == "unsupported_casualty"
    assert check_unsupported_intents("How many people need rescue?") == "unsupported_casualty"
    assert check_unsupported_intents("Kati manche ghayte bhaye?") == "unsupported_casualty"


def test_adversarial_destruction_rejected():
    assert check_unsupported_intents("Is this bridge destroyed?") == "unsupported_destruction"
    assert check_unsupported_intents("Did the bridge collapse completely?") == "unsupported_destruction"


def test_adversarial_evacuation_rejected():
    assert check_unsupported_intents("Issue an alert to evacuate now!") == "unsupported_evacuation"
    assert check_unsupported_intents("When will the flood wave arrive?") == "unsupported_evacuation"


def test_numeric_validator():
    # Only numbers in allowed list are accepted
    allowed = [12.5, 450.0, 3]
    valid_text = "The flooded area is 12.5 km² affecting 450 buildings."
    assert validate_numeric_claims(valid_text, allowed) is True

    hallucinated_text = "The flooded area is 999.0 km² affecting 5000 buildings."
    assert validate_numeric_claims(hallucinated_text, allowed) is False


def test_bilingual_template_rendering():
    slots = {
        "run_id": "test_run_1",
        "water_area_sq_km": 15.2,
        "water_area_m2": 15200000,
        "debris_area_sq_km": 2.1,
        "perm_area_sq_km": 3.4
    }
    en_text = render_response("hazard_summary", "en", slots)
    ne_text = render_response("hazard_summary", "ne", slots)

    assert "15.2 km²" in en_text or "15.2" in en_text
    assert "१५.२" in ne_text or "15.2" in ne_text
    assert "सेन्टिनेल-१" in ne_text


def test_execute_copilot_query_end_to_end():
    q_adv = CopilotQuery(
        question="How many people were killed in the flood wave?",
        language="en",
        scenario=RoutingScenario.PRECAUTIONARY
    )
    ans_adv = execute_copilot_query("test_run_1", q_adv)
    assert ans_adv.fallback_used is True
    assert "Scope Limitation" in ans_adv.answer
    assert len(ans_adv.fact_ids) == 0

    q_adv_ne = CopilotQuery(
        question="पुल पूर्ण रूपमा भत्किएको हो?",
        language="ne",
        scenario=RoutingScenario.PRECAUTIONARY
    )
    ans_adv_ne = execute_copilot_query("test_run_1", q_adv_ne)
    assert ans_adv_ne.fallback_used is True
    assert "प्रणालीगत सीमा" in ans_adv_ne.answer

