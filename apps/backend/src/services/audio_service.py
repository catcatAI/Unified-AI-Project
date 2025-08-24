import numpy as np
import wave
import io
import logging
import hashlib
import asyncio
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from src.config_loader import is_demo_mode

logger = logging.getLogger(__name__)

class AudioService:
    """音頻服務：提供語音識別、語音合成、情感分析等多模態處理能力"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.peer_services = {}  # 其他多模態服務的引用
        self.processing_history = []  # 處理歷史記錄
        
        # 初始化音頻處理配置
        self.audio_config = self.config.get('audio_config', {
            'sample_rate': 44100,
            'supported_languages': ['en-US', 'zh-CN', 'zh-TW', 'ja-JP'],
            'default_voice': 'neural_voice_1',
            'sentiment_analysis_enabled': True,
            'emotion_detection_enabled': True
        })
        
        logger.info("Audio Service initialized with enhanced capabilities")

    def set_peer_services(self, peer_services: Dict[str, Any]):
        """設置其他多模態服務的引用"""
        self.peer_services = peer_services
        logger.debug(f"Audio Service connected to peer services: {list(peer_services.keys())}")

    async def speech_to_text(self, audio_data: bytes, language: str = "en-US", 
                           enhanced_features: bool = False) -> Dict[str, Any]:
        """
        將語音音頻數據轉換為文本。增強版本支持更多特徵。
        """
        processing_id = self._generate_processing_id(audio_data)
        
        logger.info(f"Audio Service: Converting speech to text (ID: {processing_id}) for language '{language}'")
        
        if not audio_data:
            return {"error": "No audio data provided", "processing_id": processing_id}
        
        try:
            result = {
                "processing_id": processing_id,
                "audio_size": len(audio_data),
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
            
            # 基本語音識別
            transcription = await self._perform_speech_recognition(audio_data, language)
            result["text"] = transcription["text"]
            result["confidence"] = transcription["confidence"]
            
            # 增強特徵
            if enhanced_features:
                if self.audio_config.get('sentiment_analysis_enabled'):
                    result["sentiment"] = await self._analyze_sentiment(transcription["text"], audio_data)
                
                if self.audio_config.get('emotion_detection_enabled'):
                    result["emotion"] = await self._detect_audio_emotion(audio_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in speech to text conversion {processing_id}: {e}")
            return {"error": str(e), "processing_id": processing_id}
    def _generate_processing_id(self, audio_data: bytes) -> str:
        """生成唯一的處理ID"""
        hash_object = hashlib.md5(audio_data)
        return f"audio_{hash_object.hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}"

    async def _perform_speech_recognition(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """執行語音識別（模擬實現）"""
        await asyncio.sleep(0.1)  # 模擬處理時間
        
        mock_texts = {
            'en-US': ["Hello, how are you today?", "Thank you for using our service."],
            'zh-CN': ["你好，今天怎麼樣？", "謝謝您使用我們的服務。"]
        }
        
        available_texts = mock_texts.get(language, mock_texts['en-US'])
        selected_text = np.random.choice(available_texts)
        
        return {
            "text": selected_text,
            "confidence": np.random.uniform(0.8, 0.98)
        }

    async def _analyze_sentiment(self, text: str, audio_data: bytes) -> Dict[str, Any]:
        """情感分析（模擬實現）"""
        await asyncio.sleep(0.05)
        
        sentiments = ["positive", "negative", "neutral"]
        selected_sentiment = np.random.choice(sentiments)
        
        return {
            "sentiment": selected_sentiment,
            "confidence": np.random.uniform(0.7, 0.95)
        }

    async def _detect_audio_emotion(self, audio_data: bytes) -> Dict[str, Any]:
        """音頻情緒檢測（模擬實現）"""
        await asyncio.sleep(0.04)
        
        emotions = ["joy", "sadness", "anger", "fear", "surprise", "calm"]
        detected_emotion = np.random.choice(emotions)
        
        return {
            "primary_emotion": detected_emotion,
            "confidence": np.random.uniform(0.7, 0.95)
        }
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """統一的處理方法，用於統一控制中心調用"""
        if isinstance(input_data, dict):
            if 'audio_data' in input_data:
                return await self.speech_to_text(
                    input_data['audio_data'],
                    input_data.get('language', 'en-US'),
                    input_data.get('enhanced_features', False)
                )
        
        return {"error": "Invalid input format for audio processing"}

    def speech_to_text_with_sentiment_analysis(self, audio_data: bytes, language: str = "en-US") -> dict:
        """
        Converts speech to text and performs sentiment analysis.
        Behavior depends on demo mode:
        - If demo mode is disabled, raise NotImplementedError (real integration not provided).
        - If demo mode is enabled, return a mock sentiment payload.
        """
        # Use global config flag via config_loader to match tests
        import os

        # Demo if config or env flag is enabled
        if is_demo_mode() or os.getenv("USE_SIMULATED_RESOURCES") == "1" or self.config.get("use_simulated_resources", False):
            return {"text": "This is a mock transcription.", "sentiment": "positive", "confidence": 0.9, "language": language}
        else:
            raise NotImplementedError("Real sentiment analysis not implemented yet. Enable demo mode or implement the actual service.")

    def text_to_speech(self, text: str, language: str = "en-US", voice: Optional[str] = None) -> Optional[bytes]:
        """
        Converts text to speech audio data.
        Mock logic: generates a sine wave.
        """
        actual_voice = voice or self.config.get("default_voice", "default_voice_id")
        print(f"AudioService: Converting text to speech: '{text[:50]}...' for language '{language}', voice '{actual_voice}'.")
        if not text:
            return None

        # Generate a sine wave as placeholder audio data
        sample_rate = 44100
        duration = 1  # seconds
        frequency = 440  # Hz
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

        return buffer.getvalue()

if __name__ == '__main__':
    audio_config = {"default_voice": "anna"}
    service = AudioService(config=audio_config)

    # Test STT (with dummy bytes)
    dummy_audio = b'\x00\x01\x02\x03\x04\x05'
    transcription = service.speech_to_text(dummy_audio)
    print(f"Transcription: {transcription}")

    # Test TTS
    text_for_speech = "Hello, this is a test of the text to speech system."
    speech_audio = service.text_to_speech(text_for_speech)
    if speech_audio:
        print(f"Generated speech audio data (length: {len(speech_audio)} bytes).")

    print("Audio Service script finished.")
