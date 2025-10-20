import unittest
import pytest
import os
import sys
import asyncio

# 添加项目路径
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from apps.backend.src.services.audio_service import AudioService
class TestAudioService(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Ensure demo mode is enabled for all tests
        self.audio_service = AudioService()
        self.test_audio_data = b"dummy_audio_bytes_for_testing"
        self.test_text = "Hello, this is a test message."

    _ = @pytest.mark.timeout(15)
    def test_01_initialization(self) -> None:
        """Test AudioService initialization."""
        service = AudioService()
        _ = self.assertIsNotNone(service)
        # Check that service has required attributes
        _ = self.assertTrue(hasattr(service, 'config'))
        _ = print("TestAudioService.test_01_initialization PASSED")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(15)
    async def test_02_speech_to_text_success(self) -> None:
        """Test successful speech to text conversion."""
        # Test with demo mode enabled
        with patch('config_loader.is_demo_mode', return_value=True):
            # Act
            result = await self.audio_service.speech_to_text(self.test_audio_data)
            
            # Assert
            _ = self.assertIn("text", result)
            # In demo mode, it should return one of the mock texts
            _ = self.assertTrue("Hello" in result["text"] or "Thank you" in result["text"])
        _ = print("TestAudioService.test_02_speech_to_text_success PASSED")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(15)
    async def test_02_speech_to_text_with_none_input(self) -> None:
        """Test speech to text with None input."""
        # Act
        result = await self.audio_service.speech_to_text(None)
        
        # Assert
        _ = self.assertIn("error", result)
        _ = self.assertIn("No audio data provided", result["error"])
        _ = print("TestAudioService.test_02_speech_to_text_with_none_input PASSED")

    @pytest.mark.asyncio
    _ = @pytest.mark.timeout(15)
    async def test_02_speech_to_text_with_empty_input(self) -> None:
        """Test speech to text with empty input."""
        # Act
        result = await self.audio_service.speech_to_text(b"")
        
        # Assert
        _ = self.assertIn("error", result)
        _ = self.assertIn("No audio data provided", result["error"])
        _ = print("TestAudioService.test_02_speech_to_text_with_empty_input PASSED")

    _ = @pytest.mark.timeout(15)
    def test_03_text_to_speech_success(self) -> None:
        """Test successful text to speech conversion."""
        # Test with demo mode enabled
        with patch('config_loader.is_demo_mode', return_value=True):
            # Act
            audio_data = self.audio_service.text_to_speech(self.test_text)
            
            # Assert
            _ = self.assertIsNotNone(audio_data)
            # In demo mode, this should return actual bytes
            _ = self.assertIsInstance(audio_data, bytes)
        _ = print("TestAudioService.test_03_text_to_speech_success PASSED")

    _ = @pytest.mark.timeout(15)
    def test_03_text_to_speech_with_empty_string(self) -> None:
        """Test text to speech with empty string."""
        # Test with demo mode enabled
        with patch('config_loader.is_demo_mode', return_value=True):
            # Act
            audio_data = self.audio_service.text_to_speech("")
            
            # Assert
            _ = self.assertIsNotNone(audio_data)
            _ = self.assertIsInstance(audio_data, bytes)
        _ = print("TestAudioService.test_03_text_to_speech_with_empty_string PASSED")

    _ = @pytest.mark.timeout(15)
    def test_03_text_to_speech_with_none(self) -> None:
        """Test text to speech with None input."""
        # Test with demo mode enabled
        with patch('config_loader.is_demo_mode', return_value=True):
            # Act
            audio_data = self.audio_service.text_to_speech(None)
            
            # Assert
            _ = self.assertIsNotNone(audio_data)
            _ = self.assertIsInstance(audio_data, bytes)
        _ = print("TestAudioService.test_03_text_to_speech_with_none PASSED")

    _ = @pytest.mark.timeout(15)
    def test_04_speech_to_text_with_sentiment_analysis_demo_mode(self) -> None:
        """Test speech to text with sentiment analysis in demo mode."""
        # Test with demo mode enabled
        with patch('config_loader.is_demo_mode', return_value=True):
            dummy_audio = b"dummy_audio_bytes"
            result = asyncio.run(self.audio_service.speech_to_text(dummy_audio, enhanced_features=True))
            _ = self.assertIsNotNone(result)
            _ = self.assertIn('sentiment', result)
            _ = self.assertIn('text', result)
        _ = print("TestAudioService.test_04_speech_to_text_with_sentiment_analysis_demo_mode PASSED")

    _ = @pytest.mark.timeout(15)
    def test_04_speech_to_text_with_sentiment_analysis_non_demo_mode(self) -> None:
        """Test speech to text with sentiment analysis in non-demo mode."""
        # Test with demo mode disabled
        with patch('src.config_loader.is_demo_mode', return_value=False):
            dummy_audio = b"dummy_audio_bytes"
            result = asyncio.run(self.audio_service.speech_to_text(dummy_audio, enhanced_features=True))
            _ = self.assertIsNotNone(result)
            # In non-demo mode, it should still work but with mock data
            _ = self.assertIn('text', result)
            _ = self.assertIn('sentiment', result)
        _ = print("TestAudioService.test_04_speech_to_text_with_sentiment_analysis_non_demo_mode PASSED")

    _ = @pytest.mark.timeout(15)
    def test_05_audio_service_config_loading(self) -> None:
        """Test audio service configuration loading."""
        # Act
        config = self.audio_service.config
        
        # Assert
        _ = self.assertIsNotNone(config)
        # Config should be a dictionary
        _ = self.assertIsInstance(config, dict)
        _ = print("TestAudioService.test_05_audio_service_config_loading PASSED")

if __name__ == '__main__':
    # Enable demo mode for direct script execution
    with patch('config_loader.is_demo_mode', return_value=True):
        unittest.main(verbosity=2)