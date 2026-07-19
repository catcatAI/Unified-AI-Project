"""
音频服务：提供语音识别、语音合成、情感分析等多模态处理能力
"""

import asyncio
import hashlib
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from core.utils import safe_error

logger = logging.getLogger(__name__)

# 聽覺注意力子系統 (auditory attention subsystem)
from core.perception.auditory_attention import AuditoryAttentionController
from core.perception.auditory_memory import AuditoryMemory
from core.perception.auditory_sampler import AudioFeatureType, AuditorySampler

try:
    from core.sync.realtime_sync import SyncEvent, sync_manager

    _SYNC_AVAILABLE = True
except ImportError:
    _SYNC_AVAILABLE = False

try:
    from system.cluster_manager import cluster_manager

    _CLUSTER_AVAILABLE = True
except ImportError:
    _CLUSTER_AVAILABLE = False

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

# faster-whisper is imported lazily inside _stt_faster_whisper() to avoid the
# very slow transformers/ctranslate2 import chain running on every module import.
_WHISPER_MODEL = None


class AudioService:
    """音頻服務：提供語音識別、聲紋辨識、聽覺注意力與場景分析能力"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.enabled = True
        self.peer_services: dict = {}
        self.processing_history: List[Dict[str, Any]] = []

        # 聽覺注意力組件 (sampler → memory → attention)
        self.sampler = AuditorySampler(self.config.get("sampler_config"))
        self.memory = AuditoryMemory(capacity=self.config.get("memory_capacity", 500))
        self.attention = AuditoryAttentionController()

        # 註冊同步事件監聽 (best-effort; skipped outside a running event loop)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._init_sync_listener())
        except RuntimeError:
            logger.debug(
                "No running event loop, sync listener will not be initialized automatically"
            )

    async def _init_sync_listener(self) -> None:
        """初始化同步監聽器"""
        if not _SYNC_AVAILABLE:
            return
        try:
            await sync_manager.register_client("audio_service", self._handle_sync_event)
            logger.info("Audio Service registered to sync manager")
        except Exception as e:  # broad exception acceptable: sync registration should not crash
            logger.error(f"Failed to register Audio Service to sync manager: {e}", exc_info=True)

    async def _handle_sync_event(self, event: "SyncEvent") -> None:
        """處理同步事件（模組開關控制）"""
        if getattr(event, "type", None) == "module_control":
            data = getattr(event, "data", {}) or {}
            if data.get("module") == "audio":
                self.enabled = data.get("enabled", True)
                logger.info(f"Audio Service enabled status changed to: {self.enabled}")

    def _generate_processing_id(self, audio_data: bytes) -> str:
        """Generate a stable processing id (audio_<hash>_<time>)."""
        hash_object = hashlib.md5(audio_data if audio_data else b"")
        return f"audio_{hash_object.hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}"

    async def scan_and_identify(self, audio_data: bytes, duration: float = 1.0) -> dict:
        """
        模擬「監聽-識別-聚焦」的聽覺鏈路：
        1. 從音頻流中採樣粒子 (Auditory Particles)
        2. 透過聲紋記憶識別每個粒子的來源 (Identify/Register)
        3. 根據注意力控制器決定當前聚焦的聲源 (Cocktail Party Effect)
        4. 返回分析結果 (整合集群矩陣運算)
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Audio system is currently disabled"}

        # 1. 採樣音頻片段
        particles = self.sampler.sample_audio_stream(audio_data, duration)

        # 2. 識別來源並更新記憶
        active_profiles = []
        for p in particles:
            if _CLUSTER_AVAILABLE:
                try:
                    feature_vector = (
                        p.feature_vector[:16]
                        if len(p.feature_vector) >= 16
                        else np.pad(
                            p.feature_vector,
                            (0, max(0, 16 - len(p.feature_vector))),
                            "constant",
                        ).tolist()
                    )
                    await cluster_manager.distribute_task("Audio", feature_vector)
                except Exception:  # cluster distribution is optional, must not block perception
                    logger.debug("Audio cluster distribution failed", exc_info=True)

            profile = self.memory.identify_or_register(
                p.feature_vector,
                metadata={
                    "is_speech": p.source_type == AudioFeatureType.SPEECH,
                    "intensity": p.intensity,
                },
            )
            # 附加即時強度用於注意力決策
            profile.intensity = p.intensity
            active_profiles.append(profile)

        # 3. 注意力決策：聚焦到誰身上？
        user_profile = self.memory.get_user_profile()
        focus_id = self.attention.decide_focus(
            active_profiles,
            user_profile_id=user_profile.profile_id if user_profile else None,
        )

        # 4. 獲取統計與焦點詳情
        focus_profile = self.memory.profiles.get(focus_id) if focus_id else None

        return {
            "status": "success",
            "processing_id": self._generate_processing_id(audio_data),
            "timestamp": datetime.now().isoformat(),
            "detected_sources_count": len(active_profiles),
            "attention_mode": self.attention.mode.name,
            "current_focus": (
                {
                    "profile_id": focus_id,
                    "name": focus_profile.name if focus_profile else "background",
                    "label": focus_profile.label if focus_profile else "noise",
                    "intensity": focus_profile.intensity if focus_profile else 0.0,
                }
                if focus_id
                else None
            ),
            "scene_stats": self.sampler.get_focus_stats(),
        }

    async def register_user_voice(self, audio_data: bytes) -> dict:
        """註冊用戶聲紋"""
        particles = self.sampler.sample_audio_stream(audio_data)
        if not particles:
            return {"status": "error", "message": "No audio particles detected"}

        # 取平均特徵作為用戶聲紋
        avg_embedding = np.mean([p.feature_vector for p in particles], axis=0)
        profile = self.memory.identify_or_register(avg_embedding, metadata={"is_speech": True})
        profile.name = "User"
        profile.label = "user"

        return {
            "status": "success",
            "profile_id": profile.profile_id,
            "name": profile.name,
        }

    async def _stt_faster_whisper(
        self, audio_data: bytes, language: Optional[str] = None
    ) -> Optional[dict]:
        """Offline STT via faster-whisper (when installed and model is loaded)."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
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
                return {
                    "text": text.strip(),
                    "language": info.language if hasattr(info, "language") else (language or "zh"),
                    "confidence": (
                        round(info.language_probability, 3)
                        if hasattr(info, "language_probability")
                        else 0.85
                    ),
                }
        except Exception as e:
            logger.debug("faster-whisper failed: %s", e)
        return None

    async def speech_to_text(self, audio_data: bytes, language: Optional[str] = None) -> dict:
        processing_id = self._generate_processing_id(audio_data)
        result = await self._stt_faster_whisper(audio_data, language)
        if result is not None:
            result.setdefault("confidence", 0.85)
            result["processing_id"] = processing_id
            return result
        if not SR_AVAILABLE:
            return {
                "processing_id": processing_id,
                "text": "",
                "confidence": 0.0,
                "error": "speech_recognition not installed (pip install SpeechRecognition)",
            }
        try:
            recognizer = sr.Recognizer()
            audio_file = sr.AudioFile(io.BytesIO(audio_data))
            with audio_file as source:
                audio = recognizer.record(source)
            lang = language or "zh-CN"
            text = recognizer.recognize_google(audio, language=lang)
            return {"processing_id": processing_id, "text": text, "confidence": 0.9}
        except sr.UnknownValueError:
            return {
                "processing_id": processing_id,
                "text": "",
                "confidence": 0.0,
                "error": "Could not understand audio",
            }
        except sr.RequestError as e:
            return {
                "processing_id": processing_id,
                "text": "",
                "confidence": 0.0,
                "error": f"Recognition request failed: {e}",
            }
        except Exception as e:
            logger.warning("Speech recognition failed: %s", e)
            return {
                "processing_id": processing_id,
                "text": "",
                "confidence": 0.0,
                "error": safe_error(e),
            }

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
            return await self.speech_to_text(
                input_data.get("audio_data", b""), input_data.get("language")
            )
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
            return {"error": safe_error(e)}

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
