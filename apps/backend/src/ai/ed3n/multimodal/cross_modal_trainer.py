# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CrossModalMapping:
    text_key: str
    image_key: Optional[str]
    audio_key: Optional[str]
    confidence: float
    last_synced: float

    def __init__(
        self,
        text_key: str,
        image_key: Optional[str] = None,
        audio_key: Optional[str] = None,
        confidence: float = 0.5,
    ):
        self.text_key = text_key
        self.image_key = image_key
        self.audio_key = audio_key
        self.confidence = min(max(confidence, 0.0), 1.0)
        self.last_synced = time.time()

    def __repr__(self) -> str:
        parts = [f"text={self.text_key}"]
        if self.image_key:
            parts.append(f"image={self.image_key}")
        if self.audio_key:
            parts.append(f"audio={self.audio_key}")
        return f"CrossModalMapping({', '.join(parts)}, " f"conf={self.confidence:.2f})"


class CrossModalTrainer:
    def __init__(self, dictionary_layer=None, core_network=None):
        self.dictionary = dictionary_layer
        self.network = core_network
        self.mappings: Dict[str, CrossModalMapping] = {}
        self._co_occurrence: Dict[Tuple[str, str], int] = {}

    def record_co_occurrence(
        self,
        text_key: str,
        image_key: Optional[str] = None,
        audio_key: Optional[str] = None,
    ) -> None:
        now = time.time()

        if image_key:
            pair = (text_key, image_key)
            self._co_occurrence[pair] = self._co_occurrence.get(pair, 0) + 1
            if text_key in self.mappings:
                self.mappings[text_key].image_key = image_key
                self.mappings[text_key].last_synced = now
            else:
                self.mappings[text_key] = CrossModalMapping(
                    text_key=text_key, image_key=image_key, confidence=0.5
                )
            logger.debug(
                "Co-occurrence recorded: %s <-> %s (count=%d)",
                text_key,
                image_key,
                self._co_occurrence[pair],
            )

        if audio_key:
            pair = (text_key, audio_key)
            self._co_occurrence[pair] = self._co_occurrence.get(pair, 0) + 1
            if text_key in self.mappings:
                self.mappings[text_key].audio_key = audio_key
                self.mappings[text_key].last_synced = now
            else:
                self.mappings[text_key] = CrossModalMapping(
                    text_key=text_key, audio_key=audio_key, confidence=0.5
                )
            logger.debug(
                "Co-occurrence recorded: %s <-> %s (count=%d)",
                text_key,
                audio_key,
                self._co_occurrence[pair],
            )

    def train_mapping(self, min_co_occurrences: int = 3) -> int:
        created = 0
        for (key_a, key_b), count in list(self._co_occurrence.items()):
            if count < min_co_occurrences:
                continue
            confidence = min(0.5 + count * 0.1, 1.0)
            text_key = key_a if key_a.startswith(("c", "g", "e", "p", "r", "l", "t")) else key_b
            modality_key = key_b if text_key == key_a else key_a

            is_image = modality_key.startswith("img_")
            is_audio = modality_key.startswith("aud_")
            mapping = self.mappings.get(text_key)
            if mapping is None:
                mapping = CrossModalMapping(
                    text_key=text_key,
                    image_key=modality_key if is_image else None,
                    audio_key=modality_key if is_audio else None,
                    confidence=confidence,
                )
                self.mappings[text_key] = mapping
                created += 1
            else:
                if is_image:
                    mapping.image_key = modality_key
                elif is_audio:
                    mapping.audio_key = modality_key
                mapping.confidence = max(mapping.confidence, confidence)
            mapping.last_synced = time.time()

        logger.info(
            "Trained %d cross-modal mappings (min_co_occurrences=%d)",
            created,
            min_co_occurrences,
        )
        return created

    def get_related_keys(self, key: str, target_modality: str) -> List[str]:
        target_modality = target_modality.lower().strip()
        results: List[str] = []

        mapping = self.mappings.get(key)
        if mapping:
            if target_modality == "image" and mapping.image_key:
                results.append(mapping.image_key)
            if target_modality == "audio" and mapping.audio_key:
                results.append(mapping.audio_key)
            if target_modality == "text":
                results.append(mapping.text_key)

        for m in self.mappings.values():
            if target_modality == "image" and m.image_key == key:
                results.append(m.text_key)
            elif target_modality == "audio" and m.audio_key == key:
                results.append(m.text_key)
            elif target_modality == "text":
                if m.image_key == key or m.audio_key == key:
                    results.append(m.text_key)

        return list(set(results))

    def synchronize_to_network(self) -> int:
        if self.network is None:
            logger.warning("No CoreNetwork available; skipping sync.")
            return 0
        synced = 0
        for mapping in self.mappings.values():
            if mapping.image_key and mapping.confidence >= 0.6:
                self.network.add_relation(
                    mapping.text_key,
                    "mapping",
                    mapping.image_key,
                    weight=mapping.confidence,
                )
                synced += 1
            if mapping.audio_key and mapping.confidence >= 0.6:
                self.network.add_relation(
                    mapping.text_key,
                    "mapping",
                    mapping.audio_key,
                    weight=mapping.confidence,
                )
                synced += 1
        logger.info("Synchronized %d cross-modal relations into network", synced)
        return synced

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.mappings)
        with_image = sum(1 for m in self.mappings.values() if m.image_key)
        with_audio = sum(1 for m in self.mappings.values() if m.audio_key)
        avg_conf = sum(m.confidence for m in self.mappings.values()) / total if total else 0.0
        return {
            "total_mappings": total,
            "with_image": with_image,
            "with_audio": with_audio,
            "avg_confidence": round(avg_conf, 4),
            "co_occurrence_pairs": len(self._co_occurrence),
        }
