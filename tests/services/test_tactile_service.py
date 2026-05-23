# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

pytestmark = pytest.mark.asyncio

_MODULE_MOCKS = {
    'core.perception.tactile_sampler': MagicMock(),
    'core.perception.tactile_memory': MagicMock(),
    'core.sync.realtime_sync': MagicMock(),
}

for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def tactile_service():
    from apps.backend.src.services.tactile_service import TactileService
    service = TactileService(config={})
    service._init_sync_listener = AsyncMock()
    return service


class TestTactileServiceInit:

    def test_initialization(self, tactile_service):
        assert tactile_service.config == {}


class TestTactileServiceModelObject:

    async def test_model_object_tactile_basic(self, tactile_service):
        result = await tactile_service.model_object_tactile(visual_data={})
        assert isinstance(result, dict)

    async def test_model_object_tactile_with_data(self, tactile_service):
        result = await tactile_service.model_object_tactile(
            visual_data={'hardness': 0.5, 'roughness': 0.3},
        )
        assert isinstance(result, dict)


class TestTactileServiceSimulateTouch:

    async def test_simulate_touch_basic(self, tactile_service):
        result = await tactile_service.simulate_touch(
            object_id='obj1', contact_point={'x': 0.5, 'y': 0.3},
        )
        assert isinstance(result, dict)

    async def test_simulate_touch_with_origin(self, tactile_service):
        result = await tactile_service.simulate_touch(
            object_id='obj1', contact_point={}, origin='User',
        )
        assert isinstance(result, dict)


class TestTactileServiceProcess:

    async def test_process_with_model_intent(self, tactile_service):
        result = await tactile_service.process({
            'model_object_tactile': True,
            'visual_data': {},
        })
        assert result is not None

    async def test_process_invalid(self, tactile_service):
        result = await tactile_service.process('invalid')
        assert 'error' in result

    async def test_process_no_intent(self, tactile_service):
        result = await tactile_service.process({})
        assert 'error' in result


class TestTactileServiceFeedback:

    async def test_model_tactile_feedback_basic(self, tactile_service):
        result = await tactile_service.model_tactile_feedback(visual_data={})
        assert isinstance(result, dict)

    async def test_trigger_physical_feedback(self, tactile_service):
        result = await tactile_service.trigger_physical_feedback(
            device_id='device1', intensity=0.5, pattern='pulse',
        )
        assert isinstance(result, dict)

    async def test_trigger_physical_feedback_disabled(self, tactile_service):
        tactile_service.enabled = False
        result = await tactile_service.trigger_physical_feedback(
            device_id='device1', intensity=0.5, pattern='pulse',
        )
        assert result.get('status') == 'disabled'
