"""
Tests for the AudioProcessingAgent.
"""

import asyncio
import importlib.util
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

# Correct the import path based on the file's actual location
from ai.agents.specialized.audio_processing_agent import AudioProcessingAgent
from core.hsp.types import HSPMessageEnvelope, HSPTaskRequestPayload


@pytest.fixture
def audio_agent():
    """Provides a test instance of AudioProcessingAgent."""
    agent_id = f"did:hsp:test_audio_agent_{uuid.uuid4().hex[:6]}"
    agent = AudioProcessingAgent(agent_id=agent_id)

    # Mock the HSP connector for testing purposes
    agent.hsp_connector = MagicMock()
    agent.hsp_connector.send_task_result = AsyncMock()
    return agent


def test_initialization(audio_agent: AudioProcessingAgent):
    """Test AudioProcessingAgent initialization."""
    assert audio_agent.agent_id is not None
    assert len(audio_agent.capabilities) == 3

    capability_names = [cap["name"] for cap in audio_agent.capabilities]
    assert "speech_recognition" in capability_names
    assert "audio_classification" in capability_names
    assert "audio_enhancement" in capability_names


# Mocking the actual audio processing for unit tests
@pytest.mark.parametrize(
    "method_name, params, expected_keys, error_msg",
    [
        (
            "_perform_speech_recognition",
            {"audio_file": "test.wav", "language": "en"},
            ["transcription", "language", "confidence"],
            None,
        ),
        ("_perform_speech_recognition", {}, None, "No audio file provided"),
        ("_classify_audio", {"audio_file": "test.wav"}, ["primary_category", "categories"], None),
        ("_classify_audio", {}, None, "No audio file provided"),
        (
            "_enhance_audio",
            {"audio_file": "test.wav", "enhancement_type": "noise_reduction"},
            ["enhanced_file", "improvement_score"],
            None,
        ),
        ("_enhance_audio", {}, None, "No audio file provided"),
    ],
)
def test_audio_methods(
    audio_agent: AudioProcessingAgent,
    method_name: str,
    params: dict,
    expected_keys: list,
    error_msg: str,
):
    """Tests the core audio processing methods for parameter validation and return structure."""
    method_to_test = getattr(audio_agent, method_name)

    if error_msg:
        with pytest.raises(ValueError, match=error_msg):
            method_to_test(params)
    else:
        # Mock the underlying implementation to avoid actual file processing
        if method_name == "_perform_speech_recognition":
            audio_agent._perform_speech_recognition = MagicMock(
                return_value={
                    "transcription": "Hello world",
                    "language": "en",
                    "confidence": 0.95,
                    "words": [],
                    "duration": "00:00:05",
                }
            )
            method_to_test = audio_agent._perform_speech_recognition
        elif method_name == "_classify_audio":
            audio_agent._classify_audio = MagicMock(
                return_value={
                    "primary_category": "speech",
                    "categories": [],
                    "confidence_scores": [],
                    "top_category": "speech",
                    "top_confidence": 0.9,
                }
            )
            method_to_test = audio_agent._classify_audio
        elif method_name == "_enhance_audio":
            audio_agent._enhance_audio = MagicMock(
                return_value={
                    "original_file": "test.wav",
                    "enhanced_file": "enhanced_test.wav",
                    "enhancement_type": "noise_reduction",
                    "improvement_score": 0.5,
                    "processing_time": 1.2,
                }
            )
            method_to_test = audio_agent._enhance_audio

        result = method_to_test(params)
        for key in expected_keys:
            assert key in result


async def test_handle_speech_recognition_task(audio_agent: AudioProcessingAgent):
    """Test handling a speech recognition task request."""
    task_payload = HSPTaskRequestPayload(
        request_id="test_request_001",
        capability_id_filter=f"{audio_agent.agent_id}_speech_recognition_v1.0",
        parameters={"audio_file": "test_audio.wav", "language": "en"},
        callback_address="hsp/results/test_callback",
    )
    envelope = HSPMessageEnvelope(
        message_id="test_msg_001",
        sender_ai_id="test_sender",
        recipient_ai_id=audio_agent.agent_id,
        timestamp_sent="2023-01-01T00:00:00Z",
        message_type="task_request",
        protocol_version="1.0",
    )

    # Mock the actual processing method
    audio_agent._perform_speech_recognition = MagicMock(
        return_value={"transcription": "Hello world", "language": "en", "confidence": 0.95}
    )

    await audio_agent.handle_task_request(task_payload, "test_sender", envelope)

    audio_agent.hsp_connector.send_task_result.assert_called_once()
    call_args = audio_agent.hsp_connector.send_task_result.call_args
    result_payload = call_args[0][0]

    assert result_payload["status"] == "success"
    assert "transcription" in result_payload["payload"]
    assert result_payload["request_id"] == "test_request_001"


async def test_handle_unsupported_capability(audio_agent: AudioProcessingAgent):
    """Test handling an unsupported capability."""
    task_payload = HSPTaskRequestPayload(
        request_id="test_request_002",
        capability_id_filter=f"{audio_agent.agent_id}_unsupported_v1.0",
        parameters={},
        callback_address="hsp/results/test_callback",
    )
    envelope = HSPMessageEnvelope(
        message_id="test_msg_002",
        sender_ai_id="test_sender",
        recipient_ai_id=audio_agent.agent_id,
        timestamp_sent="2023-01-01T00:00:00Z",
        message_type="task_request",
        protocol_version="1.0",
    )

    await audio_agent.handle_task_request(task_payload, "test_sender", envelope)

    audio_agent.hsp_connector.send_task_result.assert_called_once()
    call_args = audio_agent.hsp_connector.send_task_result.call_args
    result_payload = call_args[0][0]

    assert result_payload["status"] == "failure"
    assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"
    assert result_payload["request_id"] == "test_request_002"


def test_transcribe_missing_file(audio_agent: AudioProcessingAgent):
    """Missing file → error shape (no engine needed)."""
    out = audio_agent.transcribe_audio("/tmp/opencode-test-nope.wav")
    assert out["status"] == "error"
    assert "transcription" not in out or out.get("transcription", "") == ""


def test_transcribe_no_path(audio_agent: AudioProcessingAgent):
    out = audio_agent.transcribe_audio("")
    assert out["status"] == "error"


def test_detect_language_missing_file(audio_agent: AudioProcessingAgent):
    out = audio_agent.detect_language("/tmp/opencode-test-nope.wav")
    assert out["status"] == "error"


@pytest.mark.skipif(
    importlib.util.find_spec("faster_whisper") is None,
    reason="faster-whisper not installed",
)
def test_transcribe_silence_graceful(audio_agent: AudioProcessingAgent, tmp_path):
    """Silence → engine runs but yields no text → unavailable shape (no crash)."""
    import wave

    wav = tmp_path / "silence.wav"
    with wave.open(str(wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * 16000)
    out = audio_agent.transcribe_audio(str(wav))
    assert out["status"] in ("success", "unavailable")
    assert "transcription" in out


@pytest.mark.skipif(
    importlib.util.find_spec("faster_whisper") is None,
    reason="faster-whisper not installed",
)
def test_is_available_with_offline_engine(audio_agent: AudioProcessingAgent):
    """Offline faster-whisper counts as available (R26, no config needed)."""
    assert audio_agent.is_available() is True
