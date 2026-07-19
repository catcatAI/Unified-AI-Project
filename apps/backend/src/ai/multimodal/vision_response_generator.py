"""
Vision Response Generator — produces natural language from CLIP classification results.

Pipeline:
  1. CLIP classify_image() -> ranked labels with confidence
  2. Map label text to ED3N dictionary key (via label->key mapping)
  3. Look up dictionary entry -> extract surface_forms (zh/en/ja)
  4. Compose response sentence using templates + surface forms

No external LLM needed — pure template + dictionary composition.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisionResponseGenerator:
    """Generates natural language descriptions from CLIP classification results.

    Uses ED3N dictionary surface_forms for concept-to-text conversion
    and simple templates for sentence construction.
    """

    def __init__(self, dictionary=None):
        self._dictionary = dictionary
        self._label_to_key: Dict[str, str] = {}
        self._templates = {
            "zh": [
                "我看到{object}{action}。",
                "這是一張{object}的圖。",
                "圖中有{object}。",
            ],
            "en": [
                "I see {object}{action}.",
                "This is a picture of {object}.",
                "There is {object} in the image.",
            ],
            "ja": [
                "{object}{action}が見えます。",
                "これは{object}の画像です。",
            ],
        }

    def register_label(self, label_text: str, dict_key: str) -> None:
        """Register a mapping from CLIP label text to dictionary key."""
        self._label_to_key[label_text.lower().strip()] = dict_key

    def register_concept(self, concept_name: str, dict_key: str, labels: List[str]) -> None:
        """Register all labels for a concept."""
        for label in labels:
            self._label_to_key[label.lower().strip()] = dict_key

    def generate_response(
        self, classifications: List[Dict[str, Any]], language: str = "zh", action: str = ""
    ) -> str:
        """Generate a natural language response from CLIP classifications.

        Args:
            classifications: Output from classify_image() or ConceptLibrary.classify()
            language: "zh", "en", or "ja"
            action: Optional action text (e.g. "在吃米" for pecking rice)

        Returns:
            Natural language string, e.g. "我看到一隻小雞在吃米。"
        """
        if not classifications:
            return self._fallback(language)

        top = classifications[0]
        label = top.get("label") or top.get("concept_name", "")
        confidence = top.get("confidence", 0.0)
        dict_key = top.get("dict_key", "")

        surface = self._get_surface_form(dict_key, language) if dict_key else None

        if surface is None:
            concept = self._extract_concept_from_label(label)
            surface = concept

        templates = self._templates.get(language, self._templates["zh"])

        if action:
            response = templates[0].format(object=surface, action=action)
        else:
            response = templates[1].format(object=surface)

        return response

    def generate_with_confidence(
        self, classifications: List[Dict[str, Any]], language: str = "zh", action: str = ""
    ) -> Dict[str, Any]:
        """Generate response with confidence metadata.

        Returns:
            {response: str, concept: str, confidence: float, dict_key: str}
        """
        if not classifications:
            return {
                "response": self._fallback(language),
                "concept": "",
                "confidence": 0.0,
                "dict_key": "",
            }

        top = classifications[0]
        label = top.get("label") or top.get("concept_name", "")
        confidence = top.get("confidence", 0.0)
        dict_key = top.get("dict_key", "")

        response = self.generate_response(classifications, language, action)
        concept = self._extract_concept_from_label(label)

        return {
            "response": response,
            "concept": concept,
            "confidence": confidence,
            "dict_key": dict_key,
        }

    def _get_surface_form(self, key: str, language: str) -> Optional[str]:
        """Get surface form from dictionary entry."""
        if self._dictionary is None or not key:
            return None
        entry = self._dictionary.entries.get(key)
        if entry is None:
            return None
        return entry.surface_forms.get(language) or entry.surface_forms.get("en")

    def _extract_concept_from_label(self, label: str) -> str:
        """Extract the core concept from a CLIP label.

        "a photo of a chicken" -> "chicken"
        "a picture of a cat sitting" -> "cat"
        """
        lower = label.lower()
        for prefix in [
            "a photo of a ",
            "a picture of a ",
            "a photo of ",
            "a picture of ",
            "a photo of the ",
            "a picture of the ",
            "a drawing of a ",
            "an illustration of a ",
        ]:
            if lower.startswith(prefix):
                label = label[len(prefix) :]
                break
        return label.split()[0] if label.split() else label

    def _fallback(self, language: str) -> str:
        if language == "en":
            return "I see an image but cannot identify specific objects."
        if language == "ja":
            return "画像が見えますが、特定の物体を識別できません。"
        return "我看到一張圖片，但無法辨識具體物體。"
