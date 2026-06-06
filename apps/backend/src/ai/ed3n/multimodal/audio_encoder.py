# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AudioEncoder:
    """
    Converts audio data to abstract dictionary keys.
    Wraps AudioSystem, AudioProcessing, AngelaRealVoice.
    """

    def __init__(self, dictionary_layer=None):
        self.dictionary = dictionary_layer
        self._audio_system = None
        self._audio_processing = None
        self._real_voice = None

    @property
    def audio_system(self):
        if self._audio_system is not None:
            return self._audio_system
        try:
            from core.engine.audio_system import AudioSystem
            self._audio_system = AudioSystem()
        except Exception as e:
            logger.warning("AudioSystem not available: %s", e)
            self._audio_system = None
        return self._audio_system

    @property
    def audio_processing(self):
        if self._audio_processing is not None:
            return self._audio_processing
        try:
            from ai.audio.audio_processing import AudioProcessing
            self._audio_processing = AudioProcessing()
        except Exception as e:
            logger.warning("AudioProcessing not available: %s", e)
            self._audio_processing = None
        return self._audio_processing

    @property
    def real_voice(self):
        if self._real_voice is not None:
            return self._real_voice
        try:
            from core.art.real_edge_tts import AngelaRealVoice
            self._real_voice = AngelaRealVoice()
        except Exception as e:
            logger.warning("AngelaRealVoice not available: %s", e)
            self._real_voice = None
        return self._real_voice

    def encode(self, audio_data: bytes, context: Optional[Dict] = None) -> List[str]:
        if not audio_data:
            return []
        ap = self.audio_processing
        if ap is not None:
            try:
                features = ap.extract_features(audio_data)
                keys: List[str] = []
                energy = features.get("energy", 0.0)
                if energy > 0.05:
                    keys.append(self._key_for_concept("loud", "energy"))
                elif energy > 0.01:
                    keys.append(self._key_for_concept("moderate", "energy"))
                else:
                    keys.append(self._key_for_concept("quiet", "energy"))
                voice_active = ap.detect_voice_activity(audio_data)
                if voice_active:
                    keys.append(self._key_for_concept("voice_detected", "voice"))
                else:
                    keys.append(self._key_for_concept("no_voice", "voice"))
                return keys
            except Exception as e:
                logger.warning("AudioProcessing failed: %s", e)
        return self._fallback_encode(audio_data)

    def encode_text_from_speech(self, audio_data: bytes) -> str:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            from io import BytesIO
            audio_file = sr.AudioFile(BytesIO(audio_data))
            with audio_file as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
        except ImportError:
            logger.warning("speech_recognition not available")
        except Exception as e:
            logger.warning("Speech recognition failed: %s", e)
        return ""

    def encode_emotion_from_voice(self, audio_data: bytes) -> List[str]:
        """
        Detect emotion from voice tone features.
        Uses audio features to estimate emotional state.
        """
        if not audio_data:
            return []
        ap = self.audio_processing
        if ap is not None:
            try:
                features = ap.extract_features(audio_data)
                energy = features.get("energy", 0.0)
                peak = features.get("peak", 0.0)
                keys: List[str] = []
                if energy > 0.1 and peak > 0.8:
                    keys.append(self._key_for_concept("excited", "emotion"))
                elif energy > 0.05 and peak > 0.5:
                    keys.append(self._key_for_concept("happy", "emotion"))
                elif energy < 0.01 and peak < 0.1:
                    keys.append(self._key_for_concept("calm", "emotion"))
                elif energy > 0.08:
                    keys.append(self._key_for_concept("angry", "emotion"))
                else:
                    keys.append(self._key_for_concept("neutral", "emotion"))
                return keys
            except Exception as e:
                logger.warning("Voice emotion detection failed: %s", e)
        return [self._key_for_concept("neutral", "emotion")]

    def _key_for_concept(self, concept: str, category: str) -> str:
        concept_str = str(concept).lower().strip()
        if not concept_str:
            return ""
        if self.dictionary is not None:
            existing = self.dictionary.encode(concept_str)
            if existing:
                return existing[0]
            key = f"aud_{category}_{abs(hash(concept_str)) % 10000}"
            self.dictionary.add_entry(
                key=key,
                surface_forms={"en": concept_str},
                contexts=[{"modality": "audio", "category": category}],
                confidence=0.7,
            )
            return key
        return f"aud_{category}_{abs(hash(concept_str)) % 10000}"

    def _fallback_encode(self, audio_data: bytes) -> List[str]:
        duration_sec = len(audio_data) / (16000 * 2)
        keys: List[str] = []
        if duration_sec < 1.0:
            keys.append(self._key_for_concept("short", "duration"))
        elif duration_sec < 5.0:
            keys.append(self._key_for_concept("medium", "duration"))
        else:
            keys.append(self._key_for_concept("long", "duration"))
        return keys

    def is_available(self) -> bool:
        return (
            self.audio_system is not None
            or self.audio_processing is not None
            or self.real_voice is not None
        )
