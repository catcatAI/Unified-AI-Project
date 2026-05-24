# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
def _async_mock():
    m = MagicMock()
    async def async_fn(*args, **kwargs):
        return m(*args, **kwargs)
    return async_fn


_MOCK_MODULES = {
    'core.perception.visual_sampler': MagicMock(),
    'core.perception.perceptual_memory': MagicMock(),
    'core.perception.attention_controller': MagicMock(),
    'core.sync.realtime_sync': MagicMock(),
    'system.cluster_manager': MagicMock(),
    'integrations.os_bridge_adapter': MagicMock(),
}
for name, mock in _MOCK_MODULES.items():
    if name not in sys.modules:
        sys.modules[name] = mock


@pytest.fixture
def vision_service():
    from apps.backend.src.services.vision_service import VisionService
    service = VisionService(config={'model_config': {'detection_confidence_threshold': 0.0}})
    service._init_sync_listener = AsyncMock()

    import services.vision_service as vs
    vs.cluster_manager.distribute_task = AsyncMock(return_value='task_123')
    vs.sync_manager.sync_event = AsyncMock()

    for method in ['_generate_image_caption', '_detect_objects', '_extract_text_ocr',
                    '_analyze_scene', '_detect_emotions', '_analyze_colors',
                    '_perform_multimodal_analysis', '_match_image_features',
                    '_identify_differences']:
        setattr(service, method, AsyncMock(return_value={}))
    service._generate_image_caption = AsyncMock(return_value='A test caption')
    service._detect_objects = AsyncMock(return_value=[{'label': 'test_object', 'confidence': 0.9}])
    service._extract_text_ocr = AsyncMock(return_value='sample text')
    service._analyze_scene = AsyncMock(return_value={'scene_type': 'indoor'})
    service._detect_emotions = AsyncMock(return_value=[{'emotion': 'happy', 'confidence': 0.8}])
    service._analyze_colors = AsyncMock(return_value=[{'color': 'blue', 'percentage': 0.5}])
    service._perform_multimodal_analysis = AsyncMock(return_value={'modality': 'visual', 'confidence': 0.9})

    return service


class TestVisionServiceInit:

    def test_initialization(self, vision_service):
        assert vision_service.enabled is True
        assert vision_service.peer_services == {}
        assert vision_service.processing_history == []
        assert vision_service.config is not None

    def test_default_config(self, vision_service):
        assert vision_service.model_config is not None
        assert 'detection_confidence_threshold' in vision_service.model_config


class TestVisionServiceAnalyzeImage:

    async def test_analyze_image_with_data(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b'test_image_bytes',
            features=['captioning'],
        )
        assert result['processing_id'].startswith('vision_')
        assert result['caption'] == 'A test caption'
        assert result['requested_features'] == ['captioning']

    async def test_analyze_image_no_data_triggers_capture(self, vision_service):
        import services.vision_service as vs
        vs.pyautogui = MagicMock()
        vs.pyautogui.screenshot = MagicMock()

        with patch.dict('sys.modules', {'pyautogui': vs.pyautogui}):
            with patch('services.vision_service.pyautogui', vs.pyautogui):
                vision_service._generate_image_caption = AsyncMock(return_value='captured')
                result = await vision_service.analyze_image(image_data=None)
                assert result.get('caption') == 'captured'

    async def test_analyze_image_all_features(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b'test',
            features=['captioning', 'object_detection', 'ocr', 'scene_analysis',
                       'emotion_detection', 'color_analysis'],
        )
        assert result['caption'] == 'A test caption'
        assert result['objects'] == [{'label': 'test_object', 'confidence': 0.9}]
        assert result['scene'] == {'scene_type': 'indoor'}
        assert result['emotions'] == [{'emotion': 'happy', 'confidence': 0.8}]
        assert result['colors'] == [{'color': 'blue', 'percentage': 0.5}]

    async def test_analyze_image_error_handling(self, vision_service):
        vision_service._generate_image_caption = AsyncMock(side_effect=Exception('Processing failed'))
        result = await vision_service.analyze_image(b'test', features=['captioning'])
        assert result['error'] == 'Processing failed'

    async def test_analyze_image_multimodal(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b'test',
            context={'text_context': 'a cat', 'audio_context': 'meow'},
        )
        assert result['multimodal_insights'] == {'modality': 'visual', 'confidence': 0.9}


class TestVisionServiceCompareImages:

    async def test_compare_images_similarity(self, vision_service):
        result = await vision_service.compare_images(b'img1', b'img2', 'similarity')
        assert isinstance(result['similarity_score'], float)
        assert 0 <= result['similarity_score'] <= 1
        assert 0.7 <= result['confidence'] <= 0.95

    async def test_compare_images_difference(self, vision_service):
        result = await vision_service.compare_images(b'img1', b'img2', 'difference')
        assert isinstance(result['difference_score'], float)
        assert result.get('difference_areas') == {}

    async def test_compare_images_feature_match(self, vision_service):
        result = await vision_service.compare_images(b'img1', b'img2', 'feature_match')
        assert result.get('matched_features') == {}
        assert 0.3 <= result.get('feature_similarity', 0) <= 0.9

    async def test_compare_images_missing_data(self, vision_service):
        result = await vision_service.compare_images(None, b'img2')
        assert result['similarity_score'] is None


class TestVisionServiceProcess:

    async def test_process_dict_input(self, vision_service):
        result = await vision_service.process({'image_data': b'test'})
        assert result.get('caption') == 'A test caption'

    async def test_process_compare_input(self, vision_service):
        result = await vision_service.process({
            'compare_images': True,
            'image_data1': b'a',
            'image_data2': b'b',
        })
        assert result.get('comparison_type') == 'similarity'
        assert isinstance(result.get('similarity_score'), float)

    async def test_process_invalid_input(self, vision_service):
        result = await vision_service.process('invalid')
        assert result['error'] == 'Invalid input format for vision processing'


class TestVisionServiceHelpers:

    async def test_initialize(self, vision_service):
        result = await vision_service.initialize()
        assert result is True

    async def test_shutdown(self, vision_service):
        result = await vision_service.shutdown()
        assert result is None

    def test_set_peer_services(self, vision_service):
        vision_service.set_peer_services({'audio': MagicMock()})
        assert 'audio' in vision_service.peer_services
