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
        """Lazy-load vision service."""
        if self._vision_service is None:
            try:
                from services.vision.vision_service import VisionService

                self._vision_service = VisionService()
            except ImportError:
                logger.debug("VisionService not available")
        return self._vision_service

    def get_hit_activations(
        self,
        input_text: str,
        image_data: Optional[bytes] = None,
        seed_answer: str = "",
    ) -> Dict[str, float]:
        """
        Compute vision hit source activations.

        Args:
            input_text: Text description or question about image.
            image_data: Optional image bytes for analysis.
            seed_answer: Seed answer for verification.

        Returns:
            Dict mapping source_id -> activation score.
        """
        result = {}

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

        # If we have image data, enhance with real analysis
        if image_data is not None:
            service = self._get_vision_service()
            if service is not None:
                try:
                    analysis = self._analyze_image(service, image_data)
                    result.update(analysis)
                except Exception as e:
                    logger.debug("Image analysis failed: %s", e)

        return result

    def _analyze_image(self, service: Any, image_data: bytes) -> Dict[str, float]:
        """Analyze image using vision service."""
        result = {}

        try:
            # Object detection
            objects = service.detect_objects(image_data)
            if objects:
                result["object_detection"] = min(1.0, len(objects) * 0.2)

            # Scene classification
            scene = service.classify_scene(image_data)
            if scene:
                result["scene_classification"] = 0.8

            # Color analysis
            colors = service.analyze_colors(image_data)
            if colors:
                result["color_analysis"] = 0.7

        except Exception as e:
            logger.debug("Vision analysis partial failure: %s", e)

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
        """Lazy-load audio service."""
        if self._audio_service is None:
            try:
                from services.audio.audio_service import AudioService

                self._audio_service = AudioService()
            except ImportError:
                logger.debug("AudioService not available")
        return self._audio_service

    def get_hit_activations(
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

        # If we have audio data, enhance with real analysis
        if audio_data is not None:
            service = self._get_audio_service()
            if service is not None:
                try:
                    analysis = self._analyze_audio(service, audio_data)
                    result.update(analysis)
                except Exception as e:
                    logger.debug("Audio analysis failed: %s", e)

        return result

    def _analyze_audio(self, service: Any, audio_data: bytes) -> Dict[str, float]:
        """Analyze audio using audio service."""
        result = {}

        try:
            # Speech recognition
            speech = service.recognize_speech(audio_data)
            if speech:
                result["speech_recognition"] = 0.9

            # Music detection
            music = service.detect_music(audio_data)
            if music:
                result["music_detection"] = 0.8

            # Emotion detection
            emotion = service.detect_emotion(audio_data)
            if emotion:
                result["emotion_in_speech"] = 0.7

        except Exception as e:
            logger.debug("Audio analysis partial failure: %s", e)

        return result
