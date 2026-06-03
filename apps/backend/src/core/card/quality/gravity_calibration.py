"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Gravity calibration — tunes TextGravityField parameters and measures
gravity effectiveness.
"""

import logging
from typing import List, Optional

from core.card.resolver.text_gravity import TextGravityField

logger = logging.getLogger(__name__)

IDEAL_LOWER = 0.6
IDEAL_UPPER = 0.85

G_CANDIDATES = [0.5, 1.0, 2.0, 5.0]
SOFTENING_CANDIDATES = [0.001, 0.01, 0.1]
REPULSION_CANDIDATES = [0.7, 0.9, 0.99]


class GravityCalibrator:
    """
    Calibrates TextGravityField parameters and measures gravity
    effectiveness (ideal range 0.6-0.85).
    """

    def __init__(self, field: Optional[TextGravityField] = None):
        self.field = field or TextGravityField()

    def measure_effectiveness(
        self, core_trait: str, candidates: List[str], chosen: List[str]
    ) -> float:
        """Execute the measure effectiveness operation."""
        if not chosen:
            return 0.0
        self.field.reset_history()
        aligned = 0
        for c in chosen:
            scored = self.field.compute_gravity(core_trait, candidates)
            if scored and scored[0][0] == c:
                aligned += 1
        return aligned / len(chosen) if chosen else 0.0

    def calibrate(
        self,
        core_trait: str,
        candidates: List[str],
        chosen: List[str],
    ) -> dict:
        """Calibrate system parameters."""
        best_score = -1.0
        best_params = {}

        for g in G_CANDIDATES:
            for s in SOFTENING_CANDIDATES:
                for r in REPULSION_CANDIDATES:
                    test_field = TextGravityField(g=g, softening=s)
                    test_field._TextGravityField__repulsion_factor = (
                        lambda c, r=r: self._repulsion(c, r)
                    )
                    aligned = 0
                    for c in chosen:
                        scored = test_field.compute_gravity(core_trait, candidates)
                        if scored and scored[0][0] == c:
                            aligned += 1
                    score = aligned / len(chosen) if chosen else 0.0
                    if score > best_score:
                        best_score = score
                        best_params = {"g": g, "softening": s, "repulsion_decay": r}

        return {"params": best_params, "effectiveness": best_score}

    def _repulsion(self, candidate: str, decay: float) -> float:
        return 0.0


__all__ = ["GravityCalibrator"]
