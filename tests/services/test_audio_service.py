# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_MOCKED_MODULES = (
    'core.perception.auditory_sampler',
    'core.perception.auditory_memory',
    'core.perception.auditory_attention',
    'core.sync.realtime_sync',
    'system.cluster_manager',
)

# Module names that bind the mocked dependencies at import time; they must be
# re-imported under the mocks and dropped again on teardown so the real modules
# are not left shadowed for other test files in the same session.
_AUDIO_SERVICE_MODULES = (
    'apps.backend.src.services.audio_service',
    'services.audio_service',
)


@pytest.fixture(autouse=True)
def _mock_audio_dependencies():
    """Inject MagicMock stand-ins for heavy perception deps for the duration of
    a single test only, restoring the real ``sys.modules`` state afterwards.

    Injecting the mocks at import time (module scope) leaks MagicMocks into
    ``sys.modules`` for the whole pytest session, causing later tests that rely
    on the real ``core.perception.*`` modules to fail.
    """
    saved = {name: sys.modules.get(name) for name in _MOCKED_MODULES + _AUDIO_SERVICE_MODULES}
    for name in _MOCKED_MODULES:
        sys.modules[name] = MagicMock()
    for name in _AUDIO_SERVICE_MODULES:
        sys.modules.pop(name, None)
    try:
        yield
    finally:
        for name in _MOCKED_MODULES + _AUDIO_SERVICE_MODULES:
            original = saved[name]
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


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
