"""
音频服务：提供语音识别、语音合成、情感分析等多模态处理能力
"""

import io
import logging
import os
import struct
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
    _WHISPER_MODEL = None
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


def _estimate_duration(audio_data: bytes) -> Optional[float]:
    """Parse WAV header to estimate duration in seconds."""
    if len(audio_data) < 44:
        return None
    try:
        if audio_data[:4] != b"RIFF":
            return None
        channels = struct.unpack("<H", audio_data[22:24])[0]
        sample_rate = struct.unpack("<I", audio_data[24:28])[0]
        bits_per_sample = struct.unpack("<H", audio_data[34:36])[0]
        data_size = len(audio_data) - 44
        bytes_per_sec = channels * sample_rate * bits_per_sample // 8
        if bytes_per_sec == 0:
            return None
        return data_size / bytes_per_sec
    except (struct.error, IndexError):
        return None


class AudioService:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.peer_services: dict = {}
        self._processing_id = 0

    async def scan_and_identify(self, audio_data: bytes, duration: Optional[float] = None) -> dict:
        if duration is None:
            duration = _estimate_duration(audio_data)
        self._processing_id += 1
        info = {"processing_id": str(self._processing_id), "status": "success", "detected_sources_count": 1}
        if duration is not None:
            info["duration_seconds"] = round(duration, 2)
            info["has_audio"] = duration > 0.1
        return info

    async def register_user_voice(self, audio_data: bytes) -> dict:
        duration = _estimate_duration(audio_data)
        return {
            "status": "success",
            "name": "User",
            "voice_id": str(uuid.uuid4())[:8],
            "duration_seconds": round(duration, 2) if duration else None,
        }

    async def _stt_faster_whisper(self, audio_data: bytes, language: Optional[str] = None) -> Optional[dict]:
        """Offline STT via faster-whisper (when installed and model is loaded)."""
        if not FASTER_WHISPER_AVAILABLE:
            return None
        global _WHISPER_MODEL
        try:
            if _WHISPER_MODEL is None:
                _WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                tmp_path = f.name
            segments, info = _WHISPER_MODEL.transcribe(tmp_path, language=language or "zh")
            text = " ".join(seg.text for seg in segments)
            os.unlink(tmp_path)
            if text.strip():
                return {"text": text.strip(), "language": info.language if hasattr(info, 'language') else (language or "zh"),
                        "confidence": round(info.language_probability, 3) if hasattr(info, 'language_probability') else 0.85}
        except Exception as e:
            logger.debug("faster-whisper failed: %s", e)
        return None

    async def speech_to_text(self, audio_data: bytes, language: Optional[str] = None) -> dict:
        self._processing_id += 1
        result = await self._stt_faster_whisper(audio_data, language)
        if result is not None:
            result["processing_id"] = str(self._processing_id)
            return result
        if not SR_AVAILABLE:
            return {
                "processing_id": str(self._processing_id),
                "text": "",
                "error": "speech_recognition not installed (pip install SpeechRecognition)",
            }
        try:
            recognizer = sr.Recognizer()
            audio_file = sr.AudioFile(io.BytesIO(audio_data))
            with audio_file as source:
                audio = recognizer.record(source)
            lang = language or "zh-CN"
            text = recognizer.recognize_google(audio, language=lang)
            return {"processing_id": str(self._processing_id), "text": text}
        except sr.UnknownValueError:
            return {"processing_id": str(self._processing_id), "text": "", "error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"processing_id": str(self._processing_id), "text": "", "error": f"Recognition request failed: {e}"}
        except Exception as e:
            logger.warning("Speech recognition failed: %s", e)
            return {"processing_id": str(self._processing_id), "text": "", "error": str(e)}

    async def text_to_speech(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        if not text:
            return None
        if not EDGE_TTS_AVAILABLE:
            logger.warning("edge-tts not installed (pip install edge-tts)")
            return None
        try:
            communicate = edge_tts.Communicate(text, voice=voice or "zh-CN-XiaoxiaoNeural")
            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            return audio_bytes if audio_bytes else None
        except Exception as e:
            logger.warning("TTS failed: %s", e)
            return None

    async def process(self, input_data: Any) -> dict:
        if not isinstance(input_data, dict):
            return {"error": "Invalid input format for audio processing"}
        if input_data.get("scan_and_identify"):
            return await self.scan_and_identify(input_data.get("audio_data", b""))
        if "speech_to_text" in input_data:
            return await self.speech_to_text(input_data.get("audio_data", b""), input_data.get("language"))
        if "text_to_speech" in input_data:
            result = await self.text_to_speech(input_data.get("text", ""), input_data.get("voice"))
            return {"audio_data": result} if result else {"error": "TTS failed"}
        return {"error": "Invalid input format for audio processing"}

    async def encode_audio(self, audio_data: bytes) -> list:
        """Encode audio into a feature vector using AudioSpectralEncoder (P15)."""
        if not audio_data:
            return []
        try:
            from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
            encoder = AudioSpectralEncoder()
            vec = encoder.encode(audio_data)
            return vec.tolist()
        except Exception as e:
            logger.warning("AudioSpectralEncoder failed: %s", e)
            return []

    async def encode_with_pipeline(self, audio_data: bytes) -> dict:
        """Run the full audio pipeline: encode → latent → decode → SNR.

        P32: Uses AudioPipeline for end-to-end processing.
        Returns dict with pipeline result including feature_vector, latent, snr.
        """
        if not audio_data:
            return {"error": "Empty audio data"}
        try:
            from ai.audio.audio_pipeline import AudioPipeline
            pipeline = AudioPipeline()
            result = pipeline.process(audio_data)
            return result
        except Exception as e:
            logger.warning("AudioPipeline failed: %s", e)
            return {"error": str(e)}

    async def batch_encode(self, audio_list: list) -> list:
        """Run AudioPipeline on multiple audio clips in batch.

        Args:
            audio_list: List of raw WAV byte arrays

        Returns:
            List of pipeline result dicts
        """
        results = []
        for audio_data in audio_list:
            result = await self.encode_with_pipeline(audio_data)
            results.append(result)
        return results

    def clear_audio_pipeline_cache(self) -> None:
        """Clear AudioPipeline internal cache."""
        try:
            from ai.audio.audio_pipeline import AudioPipeline
            p = AudioPipeline()
            p.clear_cache()
        except Exception as e:
            logger.debug("Clear cache failed: %s", e)

    def set_peer_services(self, services: dict) -> None:
        self.peer_services = services
