"""Validation rules, fact slot guards, and adversarial question detectors for AI copilot."""

import re
from typing import Any, Dict, List, Optional, Tuple


UNSUPPORTED_PATTERNS = {
    "casualty": re.compile(r"(\b(casualt|death|died|injured|people need rescue|victim|population|killed|manche|ghayte|mirtyu)\b|मान्छे|मृत्यु|घाइते)", re.IGNORECASE),
    "destruction": re.compile(r"(\b(destroyed|collapse|collapsed|structural failure|bridge failure|is.*destroyed|bhatkiyeko|nash)\b|भत्किएको|भत्केको|नष्ट)", re.IGNORECASE),
    "evacuation": re.compile(r"(\b(evacuate now|sound alarm|dispatch rescue|arrival time|arrive|wave arrive|kaba aipugcha)\b|खाली गराउनु|उद्धार पठाउनु)", re.IGNORECASE),
}


def check_unsupported_intents(question: str) -> Optional[str]:
    """Check if the user question attempts to solicit ungrounded or out-of-scope claims."""
    if UNSUPPORTED_PATTERNS["casualty"].search(question):
        return "unsupported_casualty"
    if UNSUPPORTED_PATTERNS["destruction"].search(question):
        return "unsupported_destruction"
    if UNSUPPORTED_PATTERNS["evacuation"].search(question):
        return "unsupported_evacuation"
    return None


def validate_numeric_claims(answer_text: str, allowed_numbers: List[float], tolerance: float = 0.05) -> bool:
    """Ensure that all numbers mentioned in an answer correspond to approved server facts."""
    # Extract numbers from text
    found_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", answer_text)
    for num_str in found_numbers:
        try:
            val = float(num_str)
            # Skip small integers used for formatting or percentages like 10%
            if val in (1, 2, 3, 10, 100):
                continue
            matched = any(abs(val - allowed) <= max(0.1, allowed * tolerance) for allowed in allowed_numbers)
            if not matched:
                return False
        except ValueError:
            continue
    return True
