# =============================================================================
# ANGELA-MATRIX: [L2] [αβγ] [B] [L1]
# =============================================================================

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CULTURE_MAP: Dict[str, str] = {
    "zh": "east_asian",
    "ja": "east_asian",
    "ko": "east_asian",
    "en": "western",
    "fr": "western",
    "de": "western",
    "es": "western",
    "pt": "western",
    "it": "western",
    "ar": "middle_eastern",
    "hi": "south_asian",
    "th": "southeast_asian",
    "vi": "southeast_asian",
    "ms": "southeast_asian",
    "id": "southeast_asian",
    "ru": "eastern_european",
}

CULTURAL_NOTES: Dict[str, List[Dict[str, str]]] = {
    "east_asian": [
        {"concept": "greeting", "note": "Bowing is traditional; direct eye contact may feel confrontational"},
        {"concept": "respect", "note": "Family names precede given names; honorifics are expected"},
        {"concept": "modesty", "note": "Self-deprecation is polite; direct refusal is often avoided"},
        {"concept": "gift", "note": "Gifts are exchanged with both hands; wrapping matters more than the gift"},
    ],
    "western": [
        {"concept": "greeting", "note": "Handshake or hug depending on familiarity; direct eye contact is expected"},
        {"concept": "respect", "note": "First names are common after brief acquaintance"},
        {"concept": "modesty", "note": "Direct 'thank you' and compliments are expected"},
        {"concept": "gift", "note": "Cards often accompany gifts; opening immediately is normal"},
    ],
    "middle_eastern": [
        {"concept": "greeting", "note": "Right hand only for handshake; 'salaam' is customary"},
        {"concept": "respect", "note": "Elders are addressed formally; public affection is restricted"},
        {"concept": "modesty", "note": "Modest dress expected; hospitality is paramount"},
        {"concept": "gift", "note": "Gifts are not opened in front of giver; avoid alcohol-related gifts"},
    ],
    "south_asian": [
        {"concept": "greeting", "note": "Namaste (palms together) is traditional; head wobble can mean agreement"},
        {"concept": "respect", "note": "Use titles + last name; elders are addressed with respect terms"},
        {"concept": "modesty", "note": "Direct 'no' is softened; hospitality is offered insistently"},
        {"concept": "gift", "note": "Gifts are given with right hand; avoid leather items for Hindu contexts"},
    ],
    "southeast_asian": [
        {"concept": "greeting", "note": "Wai (palms pressed) in Thailand; smile is used to mask discomfort"},
        {"concept": "respect", "note": "Hierarchy matters; head is sacred, feet are low"},
        {"concept": "modesty", "note": "Loud or confrontational speech is avoided; saving face is key"},
        {"concept": "gift", "note": "Gifts are not opened immediately; use both hands to give or receive"},
    ],
    "eastern_european": [
        {"concept": "greeting", "note": "Firm handshake with eye contact; remove gloves before shaking"},
        {"concept": "respect", "note": "Use patronymic or title + last name until invited for first name"},
        {"concept": "modesty", "note": "Direct communication style; pessimism can be a form of bonding"},
        {"concept": "gift", "note": "Flowers in odd numbers (even = funeral); no yellow flowers"},
    ],
}


def detect_culture(language_code: str = "", text: str = "") -> str:
    """Detect cultural region from language code or text analysis."""
    if language_code:
        code = language_code.split("-")[0].lower()[:2]
        if code in CULTURE_MAP:
            return CULTURE_MAP[code]
    if text:
        cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        hangul_count = sum(1 for c in text if "\uac00" <= c <= "\ud7af")
        hiragana_count = sum(1 for c in text if "\u3040" <= c <= "\u309f")
        katakana_count = sum(1 for c in text if "\u30a0" <= c <= "\u30ff")
        arabic_count = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
        # Japanese: Hiragana or Katakana presence indicates Japanese
        if hiragana_count > 0 or katakana_count > 0 or hangul_count > len(text) * 0.3:
            return "east_asian"
        if cjk_count > len(text) * 0.3:
            return "east_asian"
        if arabic_count > len(text) * 0.3:
            return "middle_eastern"
    return "western"


class CulturalContextModule:
    """Provides cultural awareness for responses based on detected user culture.

    Wires into ChatService to inject cultural context into the merged context
    before LLM inference.
    """

    def __init__(self):
        self._culture_cache: Dict[str, str] = {}

    def detect(self, language_code: str = "", text: str = "") -> str:
        """Detect culture and cache result."""
        key = f"{language_code}:{text[:50]}"
        if key in self._culture_cache:
            return self._culture_cache[key]
        result = detect_culture(language_code, text)
        self._culture_cache[key] = result
        if len(self._culture_cache) > 256:
            self._culture_cache.clear()
        return result

    def get_notes(self, culture: str) -> List[Dict[str, str]]:
        """Get cultural notes for a cultural region."""
        return CULTURAL_NOTES.get(culture, [])

    def get_greeting_advice(self, culture: str) -> str:
        """Get greeting advice for a given culture."""
        notes = self.get_notes(culture)
        for n in notes:
            if n["concept"] == "greeting":
                return n["note"]
        return ""

    def enrich_context(self, context: dict, user_message: str,
                       language_code: str = "") -> dict:
        """Inject cultural context into the given context dict."""
        culture = self.detect(language_code, user_message)
        notes = self.get_notes(culture)
        if notes:
            ctx = dict(context) if context else {}
            ctx["cultural_context"] = {
                "region": culture,
                "notes": notes,
            }
            return ctx
        return context
