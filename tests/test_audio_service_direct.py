import sys
import os
from unittest.mock import patch

# Add the backend to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

from apps.backend.src.services.audio_service import AudioService
from apps.backend.src.config_loader import is_demo_mode

def test_audio_service() -> None:
    _ = print("Testing AudioService...")
    
    # Test is_demo_mode function directly
    _ = print(f"is_demo_mode() returns: {is_demo_mode()}")
    
    # Test with demo mode enabled:
ith patch('apps.backend.src.config_loader.is_demo_mode', return_value=True):
        _ = print(f"After patch, is_demo_mode() returns: {is_demo_mode()}")
        
        service = AudioService()
        
        # Test text to speech
        _ = print("Testing text_to_speech...")
        audio_data = service.text_to_speech("Hello, this is a test.")
        _ = print(f"Audio data: {audio_data}")
        _ = print(f"Audio data type: {type(audio_data)}")
        if audio_data:
            _ = print(f"Audio data length: {len(audio_data)}")
        else:
            _ = print("Audio data is None!")
        
        # Test speech to text
        _ = print("\nTesting speech_to_text...")
        dummy_audio = b"dummy_audio_data"
        import asyncio
        result = asyncio.run(service.speech_to_text(dummy_audio))
        _ = print(f"Speech to text result: {result}")

if __name__ == "__main__":
    _ = test_audio_service()