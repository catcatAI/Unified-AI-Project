import numpy as np
import wave
import io

class AudioService:
    def __init__(self, config: dict = None):
        self.config = config or {}
        # Initialize STT/TTS engines based on config
        print("AudioService: Initialized.")

    def speech_to_text(self, audio_data: bytes, language: str = "en-US") -> str | None:
        """
        Converts speech audio data to text.
        Mock logic.
        """
        print(f"AudioService: Converting speech to text for language '{language}'. Input data length: {len(audio_data) if audio_data else 0} bytes.")
        if not audio_data:
            return None
        return "This is a mock transcription."

    def speech_to_text_with_sentiment_analysis(self, audio_data: bytes, language: str = "en-US") -> dict:
        """
        Converts speech to text and performs sentiment analysis.
        Behavior depends on demo mode:
        - If demo mode is disabled, raise NotImplementedError (real integration not provided).
        - If demo mode is enabled, return a mock sentiment payload.
        """
        if self.config.use_simulated_resources:
            return {"text": "This is a mock transcription.", "sentiment": "positive", "confidence": 0.9, "language": "en-US"}
        else:
            raise NotImplementedError("Real sentiment analysis not implemented yet. Enable demo mode or implement the actual service.")

    def text_to_speech(self, text: str, language: str = "en-US", voice: str = None) -> bytes | None:
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
