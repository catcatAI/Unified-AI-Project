"""
音頻服務：提供語音識別、語音合成、情感分析等多模態處理能力 (SKELETON)
"""

import logging
import asyncio
import hashlib # type: ignore
import wave # type: ignore
import numpy as np # type: ignore
import io
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple

from core.perception.auditory_sampler import AuditorySampler, AudioFeatureType
from core.perception.auditory_memory import AuditoryMemory, VoiceprintProfile
from core.perception.auditory_attention import AuditoryAttentionController, AuditoryAttentionMode
from core.sync.realtime_sync import sync_manager, SyncEvent
from system.cluster_manager import cluster_manager, PrecisionLevel

logger = logging.getLogger(__name__)

class AudioService:
    """音頻服務：提供語音識別、聲紋辨識、聽覺注意力與場景分析能力"""

    def __init__(self, config: Optional[dict] = None) -> None:
        self.config = config or {}
        self.enabled = True
        self.peer_services: Dict[str, Any] = {}
        self.processing_history: List[Dict[str, Any]] = []
        
        # 初始化聽覺組件
        self.sampler = AuditorySampler(self.config.get('sampler_config'))
        self.memory = AuditoryMemory(capacity=self.config.get('memory_capacity', 500))
        self.attention = AuditoryAttentionController()

        self.audio_config = self.config.get('audio_config', {
            'sample_rate': 44100,
            'supported_languages': ['en-US', 'zh-CN'],
            'default_voice': 'neural_voice_1',
            'sentiment_analysis_enabled': True,
            'emotion_detection_enabled': True
        })
        
        # 註冊同步事件監聽
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._init_sync_listener())
        except RuntimeError:
            # No running event loop, this is fine during import or sync tests
            logger.debug("No running event loop, sync listener will not be initialized automatically")
        
        logger.info("Audio Service Skeleton Initialized")

    async def _init_sync_listener(self):
        """初始化同步監聽器"""
        try:
            await sync_manager.register_client("audio_service", self._handle_sync_event)
            logger.info("Audio Service registered to sync manager")
        except Exception as e:
            logger.error(f"Failed to register Audio Service to sync manager: {e}")

    async def _handle_sync_event(self, event: SyncEvent):
        """處理同步事件"""
        if event.type == "module_control":
            module = event.data.get("module")
            enabled = event.data.get("enabled")
            if module == "audio":
                self.enabled = enabled
                logger.info(f"Audio Service enabled status changed to: {enabled}")

    def set_peer_services(self, peer_services: Dict[str, Any]):
        self.peer_services = peer_services
        logger.debug(f"Audio Service connected to peer services: {list(peer_services.keys())}")

    async def scan_and_identify(self, audio_data: bytes, duration: float = 1.0) -> Dict[str, Any]:
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
        
        # 2. 識別來源並更新記憶 (整合集群矩陣運算，Audio 預設為 FP8, 4x4)
        active_profiles = []
        for p in particles:
            # 將特徵向量發送到集群進行處理 (4x4 矩陣，16個元素)
            # 確保向量長度符合精度圖譜的 4x4 要求
            feature_vector = p.feature_vector[:16] if len(p.feature_vector) >= 16 else np.pad(p.feature_vector, (0, max(0, 16 - len(p.feature_vector))), 'constant').tolist()
            
            task_id = await cluster_manager.distribute_task("Audio", feature_vector)
            logger.debug(f"Audio Matrix Task distributed: {task_id} (Precision: FP8, Dim: 4x4)")

            profile = self.memory.identify_or_register(
                p.feature_vector, 
                metadata={
                    "is_speech": p.source_type == AudioFeatureType.SPEECH,
                    "intensity": p.intensity
                }
            )
            # 附加即時強度用於注意力決策
            profile.intensity = p.intensity 
            active_profiles.append(profile)
            
        # 3. 注意力決策：聚焦到誰身上？
        user_profile = self.memory.get_user_profile()
        focus_id = self.attention.decide_focus(
            active_profiles, 
            user_profile_id=user_profile.profile_id if user_profile else None
        )
        
        # 4. 獲取統計與焦點詳情
        focus_profile = self.memory.profiles.get(focus_id) if focus_id else None
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "detected_sources_count": len(active_profiles),
            "attention_mode": self.attention.mode.name,
            "current_focus": {
                "profile_id": focus_id,
                "name": focus_profile.name if focus_profile else "background",
                "label": focus_profile.label if focus_profile else "noise",
                "intensity": focus_profile.intensity if focus_profile else 0.0
            } if focus_id else None,
            "scene_stats": self.sampler.get_focus_stats()
        }

    async def register_user_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """註冊用戶聲紋"""
        particles = self.sampler.sample_audio_stream(audio_data)
        if not particles:
            return {"status": "error", "message": "No audio particles detected"}
            
        # 取平均特徵作為用戶聲紋
        avg_embedding = np.mean([p.feature_vector for p in particles], axis=0)
        profile = self.memory.identify_or_register(
            avg_embedding, 
            metadata={"is_speech": True}
        )
        profile.name = "User"
        profile.label = "user"
        
        return {
            "status": "success",
            "profile_id": profile.profile_id,
            "name": profile.name
        }

    async def speech_to_text(self, audio_data: bytes, language: str = "en-US", enhanced_features: bool = False) -> Dict[str, Any]:
        processing_id = self._generate_processing_id(audio_data)
        logger.info(f"Audio Service: Converting speech to text (ID: {processing_id}) for language '{language}'")
        return {"text": "mock transcription", "confidence": 0.9, "processing_id": processing_id}

    def _generate_processing_id(self, audio_data: bytes) -> str:
        hash_object = hashlib.md5(audio_data if audio_data else b"")
        return f"audio_{hash_object.hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}"

    async def _perform_speech_recognition(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"text": "This is a mock transcription.", "confidence": 0.9}

    async def _analyze_sentiment(self, text: str, audio_data: bytes) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"sentiment": "neutral", "confidence": 0.7}

    async def _detect_audio_emotion(self, audio_data: bytes) -> Dict[str, Any]:
        await asyncio.sleep(0.04)
        return {"primary_emotion": "calm", "confidence": 0.6}

    async def process(self, input_data: Any) -> Dict[str, Any]:
        if isinstance(input_data, dict) and 'audio_data' in input_data:
            return await self.speech_to_text(input_data['audio_data'], input_data.get('language', 'en-US'))
        return {"error": "Invalid input format for audio processing"}

    async def text_to_speech(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        if text is None:
            text = ""
        logger.info(f"Audio Service: Converting text to speech for '{text[:50]}...'")
        return self._generate_demo_speech_audio(text, voice)

    def _generate_demo_speech_audio(self, text: str, voice: Optional[str] = None) -> bytes:
        sample_rate = self.audio_config.get('sample_rate', 44100)
        duration = min(len(text) * 0.1, 5.0)
        frequency = 440
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, False)
        amplitude = np.iinfo(np.int16).max * 0.5
        data = amplitude * np.sin(2 * np.pi * frequency * t)

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(data.astype(np.int16).tobytes())
        buffer.seek(0)
        return buffer.read()
