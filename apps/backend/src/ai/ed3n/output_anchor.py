# =============================================================================
# ANGELA-MATRIX: [L3] [αγ] [B] [L1]
# =============================================================================

import copy
import logging
from typing import Any, Dict, List, Optional

from .dictionary_layer import DictionaryEntry, DictionaryLayer

logger = logging.getLogger(__name__)


def anchored_decode(
    network_output: Dict[str, float],
    original_input_keys: List[str],
    dictionary: DictionaryLayer,
    top_k_anchors: int = 3,
    top_k_network: int = 5,
) -> str:
    if not network_output:
        network_output = {}
    if not original_input_keys:
        original_input_keys = []
    anchor_pool: List[Dict[str, Any]] = []
    seen_keys: set = set()

    for key in original_input_keys:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entry = dictionary.entries.get(key)
        if entry is None:
            continue
        anchor_pool.append(
            {"key": key, "entry": entry, "weight": 1.0, "source": "anchor"}
        )

    sorted_network = sorted(
        network_output.items(), key=lambda x: x[1], reverse=True
    )
    for key, score in sorted_network:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entry = dictionary.entries.get(key)
        if entry is None:
            continue
        anchor_pool.append(
            {"key": key, "entry": entry, "weight": score, "source": "network"}
        )

    top_anchors = sorted(
        [a for a in anchor_pool if a["source"] == "anchor"],
        key=lambda x: x["weight"],
        reverse=True,
    )[:top_k_anchors]

    top_network = sorted(
        [a for a in anchor_pool if a["source"] == "network"],
        key=lambda x: x["weight"],
        reverse=True,
    )[:top_k_network]

    combined: Dict[str, Dict[str, Any]] = {}
    for item in top_anchors + top_network:
        key = item["key"]
        if key not in combined:
            combined[key] = item
        else:
            combined[key]["weight"] = max(
                combined[key]["weight"], item["weight"]
            )

    scored = sorted(
        combined.values(), key=lambda x: x["weight"], reverse=True
    )

    parts: List[str] = []
    seen_surfaces: set = set()
    for item in scored:
        entry: DictionaryEntry = item["entry"]
        zh = entry.surface_forms.get("zh")
        en = entry.surface_forms.get("en")
        surface = zh or en or item["key"]
        if surface in seen_surfaces:
            continue
        seen_surfaces.add(surface)
        parts.append(surface)

    return " ".join(parts) if parts else ""


class ResponseAnchorValidator:
    def __init__(self, dictionary: DictionaryLayer, max_drift: float = 0.5):
        self.dictionary = dictionary
        self.max_drift = max_drift

    def validate(
        self,
        response: str,
        anchored_keys: List[str],
        response_keys: Optional[List[str]] = None,
    ) -> bool:
        if not response.strip():
            logger.warning("Empty response rejected.")
            return False

        drift = self.measure_drift(anchored_keys, response_keys)
        if drift > self.max_drift:
            logger.info(
                "Response drift %.2f exceeds max %.2f; rejecting.",
                drift,
                self.max_drift,
            )
            return False

        return True

    def measure_drift(
        self,
        anchored_keys: List[str],
        response_keys: Optional[List[str]] = None,
    ) -> float:
        if not anchored_keys or not response_keys:
            return 1.0

        anchored_set = set(anchored_keys)
        response_set = set(response_keys)
        if not anchored_set:
            return 1.0

        overlap = anchored_set & response_set
        if not overlap:
            anchored_syns: set = set()
            for ak in anchored_set:
                entry = self.dictionary.entries.get(ak)
                if entry:
                    anchored_syns.update(
                        entry.relations.get("synonym", [])
                    )
                    anchored_syns.update(
                        entry.relations.get("mapping", [])
                    )

            expanded_set = anchored_set | anchored_syns
            overlap = response_set & expanded_set

        if not overlap:
            return 1.0

        drift = 1.0 - (len(overlap) / max(len(anchored_set), 1))
        return min(max(drift, 0.0), 1.0)

    def reject_response(
        self,
        response: str,
        anchored_keys: List[str],
        response_keys: Optional[List[str]] = None,
    ) -> bool:
        valid = self.validate(response, anchored_keys, response_keys)
        return not valid
