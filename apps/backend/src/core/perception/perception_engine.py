"""
PerceptionEngine — unified perception entry point.
Wraps existing visual/auditory/tactile samplers + attention controller.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from core.perception.attention_controller import AttentionController, AttentionMode
from core.perception.auditory_sampler import AuditorySampler
from core.perception.tactile_sampler import TactileSampler
from core.perception.visual_sampler import VisualSampler

logger = logging.getLogger(__name__)


class PerceptionEngine:
    """
    Unified perception engine — the single entry point for all sensory input.

    Delegates to modality-specific samplers based on attention focus.
    Computes confidence from sampler output quality with temporal smoothing.
    Computes saliency via attention controller with modality-specific biases.
    Detects and resolves cross-modal conflicts by highest confidence.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.attention = AttentionController()
        self.visual = VisualSampler(self.config.get("visual"))
        self.auditory = AuditorySampler(self.config.get("auditory"))
        self.tactile = TactileSampler(self.config.get("tactile"))
        self._history_window = self.config.get("history_window", 5)
        self._confidence_history: Dict[str, List[float]] = {}
        self._saliency_history: Dict[str, List[float]] = {}
        self._modality_weights = {
            "visual": self.config.get("visual_weight", 1.0),
            "auditory": self.config.get("auditory_weight", 0.8),
            "tactile": self.config.get("tactile_weight", 0.6),
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unified perception processing."""
        start = time.perf_counter()
        modality = input_data.get("type", "unknown")
        source = input_data.get("source", "unknown")
        data = input_data.get("data", {})

        if modality == "visual":
            perceived = self._process_visual(data)
        elif modality == "auditory":
            perceived = self._process_auditory(data)
        elif modality == "tactile":
            perceived = self._process_tactile(data)
        else:
            perceived = {"raw": data, "modality": modality}

        confidence = self._compute_confidence(modality, perceived)
        saliency = self._compute_saliency(modality, perceived, data)

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "perceived_data": perceived,
            "confidence": confidence,
            "saliency_score": saliency,
            "processing_time_ms": round(elapsed, 2),
            "source": source,
        }

    def decide_focus(self, input_data: Dict[str, Any]) -> AttentionMode:
        """Multi-modal attention focus with saliency-aware decision."""
        modality = input_data.get("type", "unknown")
        candidates = input_data.get("candidates", [])
        visual_data = input_data.get("data", {}).get("visual_data")

        if visual_data is not None:
            try:
                self.attention.compute_saliency_map(visual_data)
            except Exception:
                logger.debug("Saliency map computation failed", exc_info=True)

        if candidates:
            self.attention.get_next_focus_point(candidates)

        if modality == "visual":
            self.attention.mode = AttentionMode.FOCUS
        elif modality == "auditory":
            self.attention.mode = AttentionMode.TRACK
        else:
            sal = self.attention.get_saliency_at(self.attention.last_focus_pos)
            self.attention.mode = AttentionMode.FOCUS if sal > 0.6 else AttentionMode.EXPLORE

        return self.attention.mode

    def _process_visual(self, data: Dict[str, Any]) -> Dict[str, Any]:
        particles = self.visual.generate_cloud()
        focus_point = self.attention.get_next_focus_point([])
        return {
            "particles": len(particles),
            "n_particles": len(particles),
            "focus": focus_point,
        }

    def _process_auditory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        audio_data = data.get("audio", b"")
        particles = self.auditory.sample_audio_stream(audio_data)
        return {
            "particles": len(particles),
            "n_particles": len(particles),
        }

    def _process_tactile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        props = self.tactile.infer_properties_from_visuals(data)
        return {
            "roughness": props.roughness,
            "hardness": props.hardness,
            "temperature": props.temperature,
            "n_particles": 3,
        }

    def _compute_confidence(self, modality: str, perceived: Dict[str, Any]) -> float:
        base = {"visual": 0.85, "auditory": 0.70, "tactile": 0.80}.get(modality, 0.5)
        n = perceived.get("n_particles", 0)
        if n > 0:
            base = 0.5 + 0.5 * min(1.0, n / 50.0)
        hist = self._confidence_history.setdefault(modality, [])
        hist.append(base)
        if len(hist) > self._history_window:
            hist.pop(0)
        return sum(hist) / len(hist) if hist else base

    def _compute_saliency(
        self, modality: str, perceived: Dict[str, Any], data: Dict[str, Any]
    ) -> float:
        base = perceived.get("saliency", 0.5)
        if modality == "visual":
            base += 0.1
        elif modality == "auditory":
            base += 0.05
        base *= self._modality_weights.get(modality, 1.0)
        sal = self.attention.get_saliency_at(self.attention.last_focus_pos)
        base = 0.7 * base + 0.3 * sal
        hist = self._saliency_history.setdefault(modality, [])
        hist.append(base)
        if len(hist) > self._history_window:
            hist.pop(0)
        return min(1.0, max(0.0, sum(hist) / len(hist) if hist else base))

    def detect_conflicts(self, perceptions: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Detect cross-modal conflicts and resolve by confidence."""
        active = {m: p for m, p in perceptions.items()
                  if p.get("confidence", 0) > 0.3}
        if len(active) < 2:
            return None
        return max(active, key=lambda m: active[m]["confidence"])


__all__ = ["PerceptionEngine"]
