import unittest
from unittest.mock import patch
import pytest
import os
import sys
import asyncio

from apps.backend.src.services.audio_service import AudioService
from apps.backend.src.config_loader import get_config, get_simulated_resources

class TestAudioService(unittest.TestCase):

    @pytest.mark.timeout(15)
    def test_01_initialization_placeholder(self):
        service = AudioService()
        self.assertIsNotNone(service)
        print("TestAudioService.test_01_initialization_placeholder PASSED")

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_02_speech_to_text_placeholder(self):
        service = AudioService()
        dummy_audio = b"dummy_audio_bytes"
        # Fix: properly await the coroutine
        result = await service.speech_to_text(dummy_audio)
        self.assertEqual(result["text"], "This is a mock transcription.")

        result_none = await service.speech_to_text(None) # Test with None input
        self.assertIn("error", result_none)
        print("TestAudioService.test_02_speech_to_text_placeholder PASSED")

    @pytest.mark.timeout(15)
    def test_03_text_to_speech_placeholder(self):
        service = AudioService()
        audio_data = service.text_to_speech("hello")
        self.assertIsNotNone(audio_data)

        audio_data_none = service.text_to_speech("") # Test with empty string
        self.assertIsNone(audio_data_none)
        print("TestAudioService.test_03_text_to_speech_placeholder PASSED")

    @pytest.mark.skip(reason="Functionality not implemented yet")
    @pytest.mark.timeout(15)
    def test_04_speech_to_text_with_sentiment_analysis(self):
        service = AudioService()
        dummy_audio = b"dummy_audio_bytes"

        # Test with demo mode disabled
        with patch('src.config_loader.is_demo_mode', return_value=False):
            with self.assertRaises(NotImplementedError):
                service.speech_to_text_with_sentiment_analysis(dummy_audio)

        # Test with demo mode enabled
        with patch('src.config_loader.is_demo_mode', return_value=True):
            result = service.speech_to_text_with_sentiment_analysis(dummy_audio)
            self.assertIsNotNone(result)
            self.assertEqual(result['sentiment'], 'positive')

        print("TestAudioService.test_04_speech_to_text_with_sentiment_analysis PASSED")


if __name__ == '__main__':
    unittest.main(verbosity=2)