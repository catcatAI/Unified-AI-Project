# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

pytestmark = pytest.mark.asyncio

_MODULE_MOCKS = {
    'core.perception.auditory_sampler': MagicMock(),
    'core.perception.auditory_memory': MagicMock(),
    'core.perception.auditory_attention': MagicMock(),
    'core.sync.realtime_sync': MagicMock(),
    'system.cluster_manager': MagicMock(),
}

for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def audio_service():
    from apps.backend.src.services.audio_service import AudioService
    service = AudioService(config={})
    service._init_sync_listener = AsyncMock()
    return service


class TestAudioServiceInit:

    def test_initialization(self, audio_service):
        assert audio_service.config == {}

    def test_default_config(self, audio_service):
        assert audio_service.config == {}


class TestAudioServiceScanIdentify:

    async def test_scan_and_identify_basic(self, audio_service):
        result = await audio_service.scan_and_identify(audio_data=b'test_audio')
        assert result['status'] == 'success'
        assert isinstance(result['detected_sources_count'], int)

    async def test_scan_and_identify_with_duration(self, audio_service):
        result = await audio_service.scan_and_identify(audio_data=b'test_audio', duration=2.0)
        assert result['status'] == 'success'

    async def test_scan_and_identify_no_data(self, audio_service):
        result = await audio_service.scan_and_identify(audio_data=b'')
        assert result['status'] == 'success'


class TestAudioServiceRegisterVoice:

    async def test_register_user_voice(self, audio_service):
        result = await audio_service.register_user_voice(audio_data=b'voice_sample')
        assert result['status'] == 'success'
        assert result['name'] == 'User'

    async def test_register_user_voice_empty(self, audio_service):
        result = await audio_service.register_user_voice(audio_data=b'')
        assert result['status'] == 'success'


class TestAudioServiceSpeechToText:

    async def test_speech_to_text_basic(self, audio_service):
        result = await audio_service.speech_to_text(audio_data=b'test_audio')
        assert 'processing_id' in result
        assert 'text' in result

    async def test_speech_to_text_empty(self, audio_service):
        result = await audio_service.speech_to_text(audio_data=b'', language='en')
        assert 'processing_id' in result


class TestAudioServiceTextToSpeech:

    async def test_text_to_speech_basic(self, audio_service):
        result = await audio_service.text_to_speech(text='Hello world')
        assert result is None or isinstance(result, bytes)

    async def test_text_to_speech_empty(self, audio_service):
        result = await audio_service.text_to_speech(text='')
        assert result is None


class TestAudioServiceProcess:

    async def test_process_with_scan_intent(self, audio_service):
        result = await audio_service.process({'scan_and_identify': True, 'audio_data': b'test'})
        assert 'processing_id' in result
        assert 'text' in result

    async def test_process_invalid_input(self, audio_service):
        result = await audio_service.process(None)
        assert result['error'] == 'Invalid input format for audio processing'

    async def test_process_empty_dict(self, audio_service):
        result = await audio_service.process({})
        assert result['error'] == 'Invalid input format for audio processing'


class TestAudioServiceHelpers:

    def test_set_peer_services(self, audio_service):
        audio_service.set_peer_services({'vision': MagicMock()})
        assert 'vision' in audio_service.peer_services
