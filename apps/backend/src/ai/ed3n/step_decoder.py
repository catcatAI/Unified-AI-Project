# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2-L3]
# =============================================================================

import logging
import math
from random import random
from typing import Dict, List, Optional

from .core_network import CoreNetwork
from .dictionary_layer import DictionaryLayer

logger = logging.getLogger(__name__)


class StepDecoder:
    def __init__(
        self,
        dictionary: DictionaryLayer,
        network: CoreNetwork,
        max_length: int = 10,
        eos_key: Optional[str] = None,
        context_window: int = 4,
        temperature: float = 0.3,
        top_k: int = 3,
        min_score: float = 0.25,
    ):
        self.dictionary = dictionary
        self.network = network
        self.max_length = max_length
        self.eos_key = eos_key
        self.context_window = context_window
        self.temperature = temperature
        self.top_k = top_k
        self.min_score = min_score

    def generate(
        self,
        network_output: Dict[str, float],
        input_keys: List[str],
        temperature: Optional[float] = None,
    ) -> List[str]:
        if not input_keys:
            return []

        temp = temperature if temperature is not None else self.temperature
        context = list(input_keys)
        output_keys: List[str] = []
        seen: set = set(context)

        for step in range(self.max_length):
            seq_output = self.network.forward_sequential(
                context, current_position=len(context) - 1, path_type="sequence"
            )
            sorted_seq = sorted(seq_output.items(), key=lambda x: x[1], reverse=True)
            net_only = {k: v for k, v in sorted_seq[:5]}

            candidates = self._score_candidates(context, net_only, seen)

            if not candidates:
                break

            best_score = max(candidates.values())
            if best_score < self.min_score:
                break

            next_key = self._sample(candidates, temp)
            if next_key is None:
                break

            if next_key == self.eos_key:
                break
            if next_key in seen:
                break

            output_keys.append(next_key)
            seen.add(next_key)
            context.append(next_key)
            if len(context) > self.context_window:
                context = context[-self.context_window :]

        return output_keys

    def _score_candidates(
        self,
        context: List[str],
        net_activations: Dict[str, float],
        seen: set,
    ) -> Dict[str, float]:
        scores: Dict[str, float] = {}

        for key, score in net_activations.items():
            if key in seen:
                continue
            scores[key] = scores.get(key, 0.0) + score * 0.6

        for ctx_key in context:
            entry = self.dictionary.entries.get(ctx_key)
            if entry is None:
                continue
            for rel_type, targets in entry.relations.items():
                weight = 0.4 if rel_type in ("synonym", "mapping") else 0.15
                for target in targets:
                    if target in seen:
                        continue
                    scores[target] = scores.get(target, 0.0) + weight * entry.confidence

        scores = {k: v for k, v in scores.items() if v >= self.min_score}
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_scores[: self.top_k])

    def _sample(self, candidates: Dict[str, float], temperature: float) -> Optional[str]:
        if not candidates:
            return None

        if temperature <= 0 or len(candidates) == 1:
            return max(candidates, key=candidates.get)

        scaled = {k: v / max(temperature, 0.01) for k, v in candidates.items()}
        max_val = max(scaled.values())
        shifted = {k: math.exp(v - max_val) for k, v in scaled.items()}
        total = sum(shifted.values())

        if total <= 0:
            return max(candidates, key=candidates.get)

        r = random() * total
        cumulative = 0.0
        for key, prob in sorted(shifted.items(), key=lambda x: x[1], reverse=True):
            cumulative += prob
            if r <= cumulative:
                return key

        return max(candidates, key=candidates.get)

    def generate_text(
        self,
        input_text: str,
        temperature: Optional[float] = None,
    ) -> str:
        input_keys = self.dictionary.encode(input_text)
        if not input_keys:
            return ""

        self.network.reset()
        network_output = self.network.forward(input_keys)

        output_keys = self.generate(network_output, input_keys, temperature)

        if not output_keys:
            return self.dictionary.decode(input_keys)

        parts: List[str] = []
        seen_surfaces: set = set()
        for key in output_keys:
            entry = self.dictionary.entries.get(key)
            if entry is None:
                continue
            zh = entry.surface_forms.get("zh")
            en = entry.surface_forms.get("en")
            surface = zh or en or key
            if surface in seen_surfaces:
                continue
            seen_surfaces.add(surface)
            parts.append(surface)

        return " ".join(parts) if parts else ""
