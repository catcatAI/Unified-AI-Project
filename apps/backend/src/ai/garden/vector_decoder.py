# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2-L3]
# =============================================================================

import logging
import math
from random import random
from typing import Dict, List, Optional

from .dictionary import VectorDictionary
from .snn_core import TensorSNNCore

logger = logging.getLogger(__name__)


class VectorDecoder:
    def __init__(
        self,
        dictionary: VectorDictionary,
        snn: TensorSNNCore,
        max_steps: int = 10,
        eos_key: Optional[str] = None,
        min_score: float = 0.15,
        temperature: float = 0.3,
    ):
        self.dictionary = dictionary
        self.snn = snn
        self.max_steps = max_steps
        self.eos_key = eos_key
        self.min_score = min_score
        self.temperature = temperature

    def generate(self, input_text: str, max_steps: Optional[int] = None) -> str:
        if not input_text or not isinstance(input_text, str):
            return ""

        input_keys = self.dictionary.encode(input_text)
        if not input_keys:
            return ""

        sequence: List[str] = list(input_keys)
        seen: set = set(sequence)
        limit = max_steps or self.max_steps

        for _ in range(limit):
            activations = self.snn.forward(sequence)
            if not activations:
                break

            candidates = {
                k: v for k, v in activations.items()
                if k not in seen and v >= self.min_score
            }
            if not candidates:
                break

            next_key = self._sample(candidates)
            if next_key is None or next_key == self.eos_key:
                break

            sequence.append(next_key)
            seen.add(next_key)

        output_keys = [k for k in sequence if k not in set(input_keys)] or sequence
        return self.dictionary.decode(output_keys[:self.dictionary.top_k])

    def _sample(self, candidates: Dict[str, float]) -> Optional[str]:
        if not candidates:
            return None
        if self.temperature <= 0 or len(candidates) == 1:
            return max(candidates, key=candidates.get)

        scaled = {k: v / max(self.temperature, 0.01) for k, v in candidates.items()}
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
        max_steps: Optional[int] = None,
    ) -> str:
        if temperature is not None:
            orig_temp = self.temperature
            self.temperature = temperature
            result = self.generate(input_text, max_steps)
            self.temperature = orig_temp
            return result
        return self.generate(input_text, max_steps)
