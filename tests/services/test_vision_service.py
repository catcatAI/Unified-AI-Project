# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _async_mock():
    m = MagicMock()

    async def async_fn(*args, **kwargs):
        return m(*args, **kwargs)

    return async_fn


_MOCK_MODULES = {
    "core.perception.visual_sampler": MagicMock(),
    "core.perception.perceptual_memory": MagicMock(),
    "core.perception.attention_controller": MagicMock(),
    "core.sync.realtime_sync": MagicMock(),
    "system.cluster_manager": MagicMock(),
    "integrations.os_bridge_adapter": MagicMock(),
}
# Only inject a mock when the REAL module cannot be imported. A blind
# sys.modules[name] = mock here permanently shadowed real modules for every
# later test in the same process (smoke instantiate tests then received a
# MagicMock where a class was expected).
import importlib

for name, mock in _MOCK_MODULES.items():
    if name not in sys.modules:
        try:
            importlib.import_module(name)
        except Exception:
            sys.modules[name] = mock


@pytest.fixture
def vision_service():
    from apps.backend.src.services.vision_service import VisionService

    service = VisionService(config={"model_config": {"detection_confidence_threshold": 0.0}})
    service._init_sync_listener = AsyncMock()

    import services.vision_service as vs

    vs.cluster_manager.distribute_task = AsyncMock(return_value="task_123")
    vs.sync_manager.sync_event = AsyncMock()

    for method in [
        "_generate_image_caption",
        "_detect_objects",
        "_extract_text_ocr",
        "_analyze_scene",
        "_detect_emotions",
        "_analyze_colors",
        "_perform_multimodal_analysis",
        "_match_image_features",
        "_identify_differences",
    ]:
        setattr(service, method, AsyncMock(return_value={}))
    service._generate_image_caption = AsyncMock(return_value="A test caption")
    service._detect_objects = AsyncMock(return_value=[{"label": "test_object", "confidence": 0.9}])
    service._extract_text_ocr = AsyncMock(return_value="sample text")
    service._analyze_scene = AsyncMock(return_value={"scene_type": "indoor"})
    service._detect_emotions = AsyncMock(return_value=[{"emotion": "happy", "confidence": 0.8}])
    service._analyze_colors = AsyncMock(return_value=[{"color": "blue", "percentage": 0.5}])
    service._perform_multimodal_analysis = AsyncMock(
        return_value={"modality": "visual", "confidence": 0.9}
    )

    return service


class TestVisionServiceInit:

    def test_initialization(self, vision_service):
        assert vision_service.enabled is True
        assert vision_service.peer_services == {}
        assert vision_service.processing_history == []
        assert vision_service.config is not None

    def test_default_config(self, vision_service):
        assert vision_service.model_config is not None
        assert "detection_confidence_threshold" in vision_service.model_config


class TestVisionServiceAnalyzeImage:

    async def test_analyze_image_with_data(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b"test_image_bytes",
            features=["captioning"],
        )
        assert result["processing_id"].startswith("vision_")
        assert result["caption"] == "A test caption"
        assert result["requested_features"] == ["captioning"]

    async def test_analyze_image_no_data_triggers_capture(self, vision_service):
        import services.vision_service as vs
        from PIL import Image

        vs.pyautogui = MagicMock()
        vs.pyautogui.screenshot = MagicMock(return_value=Image.new("RGB", (64, 64)))

        with patch.dict("sys.modules", {"pyautogui": vs.pyautogui}):
            with patch("services.vision_service.pyautogui", vs.pyautogui):
                vision_service._generate_image_caption = AsyncMock(return_value="captured")
                result = await vision_service.analyze_image(image_data=None)
                assert result.get("caption") == "captured"

    async def test_analyze_image_all_features(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b"test",
            features=[
                "captioning",
                "object_detection",
                "ocr",
                "scene_analysis",
                "emotion_detection",
                "color_analysis",
            ],
        )
        assert result["caption"] == "A test caption"
        assert result["objects"] == [{"label": "test_object", "confidence": 0.9}]
        assert result["scene"] == {"scene_type": "indoor"}
        assert result["emotions"] == [{"emotion": "happy", "confidence": 0.8}]
        assert result["colors"] == [{"color": "blue", "percentage": 0.5}]

    async def test_analyze_image_error_handling(self, vision_service):
        vision_service._generate_image_caption = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        result = await vision_service.analyze_image(b"test", features=["captioning"])
        assert result["error"] == "Processing failed"

    async def test_analyze_image_multimodal(self, vision_service):
        result = await vision_service.analyze_image(
            image_data=b"test",
            context={"text_context": "a cat", "audio_context": "meow"},
        )
        assert result["multimodal_insights"] == {"modality": "visual", "confidence": 0.9}


class TestVisionServiceCompareImages:

    @pytest.mark.parametrize(
        "img1,img2,mode,checks",
        [
            (
                b"img1",
                b"img2",
                "similarity",
                [
                    lambda r: isinstance(r["similarity_score"], float),
                    lambda r: 0 <= r["similarity_score"] <= 1,
                    lambda r: 0.7 <= r["confidence"] <= 1.0,
                ],
            ),
            (
                b"img1",
                b"img2",
                "difference",
                [
                    lambda r: isinstance(r["difference_score"], float),
                    lambda r: isinstance(r.get("difference_areas", []), list),
                ],
            ),
            (
                b"img1",
                b"img2",
                "feature_match",
                [
                    lambda r: r.get("matched_features") is None
                    or isinstance(r["matched_features"], dict),
                    lambda r: 0.3 <= r.get("feature_similarity", 0) <= 1.0,
                ],
            ),
            (
                None,
                b"img2",
                "similarity",
                [
                    lambda r: r["similarity_score"] is None,
                ],
            ),
        ],
    )
    async def test_compare_images(self, vision_service, img1, img2, mode, checks):
        result = await vision_service.compare_images(img1, img2, mode)
        for check in checks:
            assert check(result)


class TestVisionServiceProcess:

    async def test_process_dict_input(self, vision_service):
        result = await vision_service.process({"image_data": b"test"})
        assert result.get("caption") == "A test caption"

    async def test_process_compare_input(self, vision_service):
        result = await vision_service.process(
            {
                "compare_images": True,
                "image_data1": b"a",
                "image_data2": b"b",
            }
        )
        assert result.get("comparison_type") == "similarity"
        assert isinstance(result.get("similarity_score"), float)

    async def test_process_invalid_input(self, vision_service):
        result = await vision_service.process("invalid")
        assert result["error"] == "Invalid input format for vision processing"


class TestVisionServiceHelpers:

    async def test_initialize(self, vision_service):
        result = await vision_service.initialize()
        assert result is True

    async def test_shutdown(self, vision_service):
        result = await vision_service.shutdown()
        assert result is True

    def test_set_peer_services(self, vision_service):
        vision_service.set_peer_services({"audio": MagicMock()})
        assert "audio" in vision_service.peer_services


class TestVideoMotionIsMeasured:
    """The video path reported a coin flip as "motion_detected"."""

    def _frame(self, color):
        from io import BytesIO

        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (64, 64), color).save(buf, format="PNG")
        return buf.getvalue()

    @pytest.mark.asyncio
    async def test_motion_is_measured_against_the_previous_frame(self):
        from services.vision_service import VisionService

        svc = VisionService()
        first = await svc.process_video_frame(self._frame((0, 0, 0)), 0)
        # The first frame has nothing to compare against.
        assert first["motion_detected"] is False
        assert first["motion_score"] == 0.0

        same = await svc.process_video_frame(self._frame((0, 0, 0)), 1)
        assert same["motion_detected"] is False

        different = await svc.process_video_frame(self._frame((255, 255, 255)), 2)
        assert different["motion_detected"] is True
        assert different["motion_score"] > 0

    @pytest.mark.asyncio
    async def test_the_motion_score_is_not_random(self):
        """The same frames must always give the same answer."""
        from services.vision_service import VisionService

        results = []
        for _ in range(3):
            svc = VisionService()
            await svc.process_video_frame(self._frame((0, 0, 0)), 0)
            result = await svc.process_video_frame(self._frame((10, 10, 10)), 1)
            results.append(result["motion_detected"])
        assert len(set(results)) == 1
