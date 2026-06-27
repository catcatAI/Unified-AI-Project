"""
PerceptionEngine — unified perception entry point.
Wraps existing visual/auditory/tactile samplers + attention controller.
"""

import logging
import time
from typing import Any, Dict, Optional

from core.perception.attention_controller import AttentionController, AttentionMode
from core.perception.auditory_sampler import AuditorySampler
from core.perception.tactile_sampler import TactileSampler
from core.perception.visual_sampler import VisualSampler

logger = logging.getLogger(__name__)


class PerceptionEngine:
    """
    Unified perception engine — the single entry point for all sensory input.

    Delegates to modality-specific samplers based on attention focus.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.attention = AttentionController()
        self.visual = VisualSampler(self.config.get("visual"))
        self.auditory = AuditorySampler(self.config.get("auditory"))
        self.tactile = TactileSampler(self.config.get("tactile"))

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unified perception processing."""
        start = time.perf_counter()
        modality = input_data.get("type", "unknown")
        source = input_data.get("source", "unknown")
        data = input_data.get("data", {})

        # Route to the correct modality sampler
        if modality == "visual":
            perceived = self._process_visual(data)
        elif modality == "auditory":
            perceived = self._process_auditory(data)
        elif modality == "tactile":
            perceived = self._process_tactile(data)
        else:
            perceived = {"raw": data, "modality": modality}

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "perceived_data": perceived,
            "confidence": perceived.get("confidence", 0.5),
            "saliency_score": perceived.get("saliency", 0.5),
            "processing_time_ms": round(elapsed, 2),
            "source": source,
        }

    def decide_focus(self, input_data: Dict[str, Any]) -> AttentionMode:
        """Determine where attention should be directed."""
        modality = input_data.get("type", "unknown")
        if modality == "visual":
            self.attention.mode = AttentionMode.FOCUS
        elif modality == "auditory":
            self.attention.mode = AttentionMode.TRACK
        else:
            self.attention.mode = AttentionMode.EXPLORE
        return self.attention.mode

    def _process_visual(self, data: Dict[str, Any]) -> Dict[str, Any]:
        particles = self.visual.generate_cloud()
        focus_point = self.attention.get_next_focus_point([])
        return {
            "particles": len(particles),
            "focus": focus_point,
            "confidence": 0.85,
            "saliency": 0.75,
        }

    def _process_auditory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        audio_data = data.get("audio", b"")
        particles = self.auditory.sample_audio_stream(audio_data)
        return {
            "particles": len(particles),
            "confidence": 0.70,
            "saliency": 0.60,
        }

    def _process_tactile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        props = self.tactile.infer_properties_from_visuals(data)
        return {
            "roughness": props.roughness,
            "hardness": props.hardness,
            "temperature": props.temperature,
            "confidence": 0.80,
            "saliency": 0.65,
        }


__all__ = ["PerceptionEngine"]
