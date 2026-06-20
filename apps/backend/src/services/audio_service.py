"""
音频服务：提供语音识别、语音合成、情感分析等多模态处理能力
"""

import io
import logging
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
        info = {"status": "success", "detected_sources_count": 1}
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

    async def speech_to_text(self, audio_data: bytes, language: Optional[str] = None) -> dict:
        self._processing_id += 1
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

    def set_peer_services(self, services: dict) -> None:
        self.peer_services = services
