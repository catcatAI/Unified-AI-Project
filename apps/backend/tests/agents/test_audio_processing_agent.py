import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from apps.backend.src.agents.audio_processing_agent import AudioProcessingAgent

@pytest.fixture
def mock_hsp_connector():
    """Fixture to provide a mock HSPConnector."""
    mock = MagicMock()
    mock.register_on_task_request_callback = MagicMock()
    mock.advertise_capability = AsyncMock()
    mock.send_task_result = AsyncMock()
    mock.is_connected = True
    return mock

@pytest.fixture
def audio_processing_agent():
    """Fixture to provide an AudioProcessingAgent instance."""
    agent = AudioProcessingAgent(
        agent_id="did:hsp:audio_processing_agent_test"
    )
    return agent

@pytest.mark.asyncio
async def test_audio_processing_agent_init(audio_processing_agent):
    """Test that the AudioProcessingAgent initializes correctly."""
    assert audio_processing_agent.agent_id == "did:hsp:audio_processing_agent_test"
    assert len(audio_processing_agent.capabilities) == 3
    capability_names = [cap['name'] for cap in audio_processing_agent.capabilities]
    assert "speech_recognition" in capability_names
    assert "audio_classification" in capability_names
    assert "audio_enhancement" in capability_names

@pytest.mark.asyncio
async def test_audio_processing_agent_perform_speech_recognition(audio_processing_agent):
    """Test the speech recognition functionality."""
    params = {
        "audio_file": "test_audio.wav",
        "language": "en"
    }
    
    result = audio_processing_agent._perform_speech_recognition(params)
    
    assert "transcription" in result
    assert "language" in result
    assert "confidence" in result
    assert "words" in result
    assert "duration" in result
    assert result["language"] == "en"
    assert isinstance(result["confidence"], float)

@pytest.mark.asyncio
async def test_audio_processing_agent_classify_audio(audio_processing_agent):
    """Test the audio classification functionality."""
    params = {
        "audio_file": "test_audio.wav"
    }
    
    result = audio_processing_agent._classify_audio(params)
    
    assert "primary_category" in result
    assert "categories" in result
    assert "confidence_scores" in result
    assert "top_category" in result
    assert "top_confidence" in result
    assert len(result["categories"]) == len(result["confidence_scores"])
    assert isinstance(result["top_confidence"], float)

@pytest.mark.asyncio
async def test_audio_processing_agent_enhance_audio(audio_processing_agent):
    """Test the audio enhancement functionality."""
    params = {
        "audio_file": "test_audio.wav",
        "enhancement_type": "noise_reduction"
    }
    
    result = audio_processing_agent._enhance_audio(params)
    
    assert "original_file" in result
    assert "enhanced_file" in result
    assert "enhancement_type" in result
    assert "improvement_score" in result
    assert "processing_time" in result
    assert result["original_file"] == "test_audio.wav"
    assert result["enhancement_type"] == "noise_reduction"

@pytest.mark.asyncio
async def test_audio_processing_agent_handle_task_request_speech_recognition(audio_processing_agent, mock_hsp_connector):
    """Test handling a speech recognition task request."""
    with patch('apps.backend.src.agents.base_agent.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('apps.backend.src.agents.base_agent.get_services') as mock_get_services:
            mock_get_services.return_value = {
                'hsp_connector': mock_hsp_connector,
                'llm_interface': MagicMock(),
                'ham_manager': MagicMock(),
                'personality_manager': MagicMock(),
                'trust_manager': MagicMock(),
                'service_discovery': MagicMock(),
                'fact_extractor': MagicMock(),
                'content_analyzer': MagicMock(),
                'learning_manager': MagicMock(),
                'emotion_system': MagicMock(),
                'crisis_system': MagicMock(),
                'time_system': MagicMock(),
                'formula_engine': MagicMock(),
                'tool_dispatcher': MagicMock(),
                'dialogue_manager': MagicMock(),
                'agent_manager': MagicMock(),
                'ai_virtual_input_service': MagicMock(),
                'audio_service': MagicMock(),
                'vision_service': MagicMock(),
                'resource_awareness_service': MagicMock(),
            }
            await audio_processing_agent._ainit()
            
            task_payload = {
                "request_id": "test_request_1",
                "capability_id_filter": "speech_recognition_v1.0",
                "parameters": {
                    "audio_file": "sample_audio.wav",
                    "language": "en"
                },
                "callback_address": "test_callback_1"
            }
            envelope = {"sender_ai_id": "test_sender"}
            
            await audio_processing_agent.handle_task_request(task_payload, "test_sender", envelope)
            
            # Verify that send_task_result was called
            assert mock_hsp_connector.send_task_result.called
            call_args = mock_hsp_connector.send_task_result.call_args
            result_payload = call_args[0][0]
            callback_topic = call_args[0][1]
            
            assert result_payload["status"] == "success"
            assert "payload" in result_payload
            assert callback_topic == "test_callback_1"

@pytest.mark.asyncio
async def test_audio_processing_agent_handle_task_request_unsupported_capability(audio_processing_agent, mock_hsp_connector):
    """Test handling a task request with an unsupported capability."""
    with patch('apps.backend.src.agents.base_agent.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('apps.backend.src.agents.base_agent.get_services') as mock_get_services:
            mock_get_services.return_value = {
                'hsp_connector': mock_hsp_connector,
                'llm_interface': MagicMock(),
                'ham_manager': MagicMock(),
                'personality_manager': MagicMock(),
                'trust_manager': MagicMock(),
                'service_discovery': MagicMock(),
                'fact_extractor': MagicMock(),
                'content_analyzer': MagicMock(),
                'learning_manager': MagicMock(),
                'emotion_system': MagicMock(),
                'crisis_system': MagicMock(),
                'time_system': MagicMock(),
                'formula_engine': MagicMock(),
                'tool_dispatcher': MagicMock(),
                'dialogue_manager': MagicMock(),
                'agent_manager': MagicMock(),
                'ai_virtual_input_service': MagicMock(),
                'audio_service': MagicMock(),
                'vision_service': MagicMock(),
                'resource_awareness_service': MagicMock(),
            }
            await audio_processing_agent._ainit()
            
            task_payload = {
                "request_id": "test_request_2",
                "capability_id_filter": "unsupported_capability_v1.0",
                "parameters": {},
                "callback_address": "test_callback_2"
            }
            envelope = {"sender_ai_id": "test_sender"}
            
            await audio_processing_agent.handle_task_request(task_payload, "test_sender", envelope)
            
            # Verify that send_task_result was called with failure
            assert mock_hsp_connector.send_task_result.called
            call_args = mock_hsp_connector.send_task_result.call_args
            result_payload = call_args[0][0]
            callback_topic = call_args[0][1]
            
            assert result_payload["status"] == "failure"
            assert "error_details" in result_payload
            assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"
            assert callback_topic == "test_callback_2"