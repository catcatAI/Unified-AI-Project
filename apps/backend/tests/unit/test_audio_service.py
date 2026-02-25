import random
import numpy as np

from src.services.audio_service import AudioService
from src.core.perception.auditory_attention import AuditoryAttentionController


def setup_module(module):
    random.seed(42)
    np.random.seed(42)


def test_speech_to_text_mock_and_processing_id_format():
    svc = AudioService()
    data = b"hello world" * 10
    out = svc._AudioService__class__ if False else None  # silence linter about private use
    result = svc.speech_to_text.__wrapped__ if hasattr(svc.speech_to_text, "__wrapped__") else None
    # run coro
    import asyncio
    got = asyncio.get_event_loop().run_until_complete(svc.speech_to_text(data, language="en-US"))

    assert set(["text", "confidence", "processing_id"]).issubset(got.keys())
    assert isinstance(got["text"], str)
    assert isinstance(got["confidence"], float)
    assert got["processing_id"].startswith("audio_")


def test_generate_demo_speech_audio_wav_signature():
    svc = AudioService()
    wav = svc._generate_demo_speech_audio("test text")
    assert isinstance(wav, (bytes, bytearray))
    # Check RIFF/WAVE signature
    assert wav[:4] == b"RIFF"
    assert b"WAVE" in wav[:16]


def test_attention_controller_prefers_higher_intensity_and_user():
    ctl = AuditoryAttentionController()

    class S:
        def __init__(self, pid, label, intensity):
            self.profile_id = pid
            self.label = label
            self.intensity = intensity

    # Higher intensity should win when no user specified
    s1 = S("a", "speaker", 0.4)
    s2 = S("b", "speaker", 0.8)
    got = ctl.decide_focus([s1, s2], user_profile_id=None)
    assert got in {"a", "b"}
    assert got == "b"

    # Reset controller to allow switching focus immediately
    ctl.reset()
    # If user id present, it should be prioritized even with lower intensity (due to user_voice_priority)
    s3 = S("user1", "speaker", 0.7)
    got2 = ctl.decide_focus([s2, s3], user_profile_id="user1")
    assert got2 == "user1"
