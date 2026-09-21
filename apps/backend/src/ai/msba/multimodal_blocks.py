# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MultimodalBlock — vision and audio processing blocks for MSBA.

Phase 1: Feature extraction (keywords + metadata)
Phase 2: Integration with existing VisionPipeline/AudioPipeline
"""

import logging
from typing import Any, Dict, List, Optional

from .types import HitSource

logger = logging.getLogger(__name__)


class VisionBlock:
    """
    Vision processing block for MSBA.

    Processes image-related inputs via feature extraction.
    """

    def __init__(self):
        self.block_id = "vision"
        self.block_name = "Vision"

        self.hit_sources = [
            HitSource("object_detection", "object"),
            HitSource("scene_classification", "scene"),
            HitSource("color_analysis", "color"),
            HitSource("spatial_relation", "spatial"),
            HitSource("text_in_image", "text"),
            HitSource("face_detection", "face"),
            HitSource("motion_detection", "motion"),
        ]

        self._vision_service = None

    def _get_vision_service(self) -> Any:
        """Lazy-load the real vision service (services.vision_service)."""
        if self._vision_service is None:
            try:
                from services.vision_service import VisionService

                self._vision_service = VisionService()
            except ImportError:
                logger.debug("VisionService not available")
        return self._vision_service

    async def get_hit_activations(
        self,
        input_text: str,
        image_data: Optional[bytes] = None,
        seed_answer: str = "",
    ) -> Dict[str, float]:
        """
        Compute vision hit source activations.

        Args:
            input_text: Text description or question about image.
            image_data: Optional image bytes for real analysis.
            seed_answer: Seed answer for verification.

        Returns:
            Dict mapping source_id -> activation score.
        """
        result: Dict[str, float] = {}

        # Text-based activation
        text_lower = input_text.lower()
        vision_keywords = [
            "image",
            "picture",
            "photo",
            "see",
            "look",
            "vision",
            "visual",
            "color",
            "object",
            "face",
            "scene",
            "video",
            "animate",
            "draw",
            "paint",
        ]
        text_score = sum(1 for kw in vision_keywords if kw in text_lower)
        text_activation = min(1.0, text_score * 0.2)

        for hs in self.hit_sources:
            result[hs.source_id] = text_activation

        # Real analysis via the project's VisionService when image data present
        if image_data:
            service = self._get_vision_service()
            if service is not None:
                try:
                    analysis = await self._analyze_image(service, image_data)
                    result.update(analysis)
                except Exception as e:
                    logger.debug("Image analysis failed: %s", e)

        return result

    async def _analyze_image(self, service: Any, image_data: bytes) -> Dict[str, float]:
        """Analyze image via the real VisionService.analyze_image API."""
        result: Dict[str, float] = {}

        analysis = await service.analyze_image(
            image_data=image_data,
            features=["objects", "scene", "colors"],
        )
        if not isinstance(analysis, dict) or analysis.get("error"):
            return result

        objects = analysis.get("objects")
        if objects:
            result["object_detection"] = min(1.0, len(objects) * 0.2)
        scene = analysis.get("scene")
        if scene:
            result["scene_classification"] = 0.8
        colors = analysis.get("colors")
        if colors:
            result["color_analysis"] = 0.7
        faces = analysis.get("faces")
        if faces:
            result["face_detection"] = 0.8
        ocr_text = analysis.get("ocr_text")
        if ocr_text:
            result["text_in_image"] = 0.8

        return result


class AudioBlock:
    """
    Audio processing block for MSBA.

    Processes audio-related inputs via feature extraction.
    """

    def __init__(self):
        self.block_id = "audio"
        self.block_name = "Audio"

        self.hit_sources = [
            HitSource("speech_recognition", "speech"),
            HitSource("music_detection", "music"),
            HitSource("noise_analysis", "noise"),
            HitSource("emotion_in_speech", "emotion"),
            HitSource("speaker_identification", "speaker"),
            HitSource("temporal_pattern", "rhythm"),
            HitSource("frequency_analysis", "frequency"),
        ]

        self._audio_service = None

    def _get_audio_service(self) -> Any:
        """Lazy-load the real audio service (services.audio_service)."""
        if self._audio_service is None:
            try:
                from services.audio_service import AudioService

                self._audio_service = AudioService()
            except ImportError:
                logger.debug("AudioService not available")
        return self._audio_service

    async def get_hit_activations(
        self,
        input_text: str,
        audio_data: Optional[bytes] = None,
        seed_answer: str = "",
    ) -> Dict[str, float]:
        """
        Compute audio hit source activations.

        Args:
            input_text: Text description or question about audio.
            audio_data: Optional audio bytes for analysis.
            seed_answer: Seed answer for verification.

        Returns:
            Dict mapping source_id -> activation score.
        """
        result = {}

        # Text-based activation
        text_lower = input_text.lower()
        audio_keywords = [
            "audio",
            "sound",
            "music",
            "hear",
            "listen",
            "voice",
            "speech",
            "song",
            "melody",
            "rhythm",
            "beat",
            "tone",
            "noise",
            "silent",
            "loud",
        ]
        text_score = sum(1 for kw in audio_keywords if kw in text_lower)
        text_activation = min(1.0, text_score * 0.2)

        for hs in self.hit_sources:
            result[hs.source_id] = text_activation

        # Real analysis via the project's AudioService when audio data present
        if audio_data:
            service = self._get_audio_service()
            if service is not None:
                try:
                    analysis = await self._analyze_audio(service, audio_data)
                    result.update(analysis)
                except Exception as e:
                    logger.debug("Audio analysis failed: %s", e)

        return result

    async def _analyze_audio(self, service: Any, audio_data: bytes) -> Dict[str, float]:
        """Analyze audio via the real AudioService APIs."""
        result: Dict[str, float] = {}

        # Speech recognition
        try:
            stt = await service.speech_to_text(audio_data)
            if isinstance(stt, dict):
                text = stt.get("text") or ""
                conf = float(stt.get("confidence") or 0.0)
                if text:
                    result["speech_recognition"] = min(1.0, conf) if conf > 0 else 0.9
        except Exception as e:
            logger.debug("Speech recognition failed: %s", e)

        # Speaker identification via the auditory scan chain
        try:
            identify = await service.scan_and_identify(audio_data)
            if isinstance(identify, dict):
                profiles = identify.get("active_profiles") or identify.get("profiles") or []
                if profiles:
                    result["speaker_identification"] = min(1.0, len(profiles) * 0.5)
        except Exception as e:
            logger.debug("Audio scan failed: %s", e)

        return result
