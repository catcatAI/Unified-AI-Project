"""
P31: Tests for VisionPipeline and VisionQualityMonitor.

Tests cover:
- VisionPipeline.process() — full end-to-end pipeline
- VisionPipeline.encode_only() — encode bypass
- VisionPipeline.decode_latent_to_pil() — decode latent
- VisionPipeline.get_latent() — encode + project only
- VisionPipeline.batch_process() — batch processing
- VisionPipeline caching (LRU, clear, cache_size)
- VisionPipeline SSIM/PSNR computation
- VisionPipeline.get_stats()
- VisionQualityMonitor.record() + report()
- VisionQualityMonitor.quality_trend()
- VisionService.encode_with_pipeline()
- VisionService.batch_encode()

Total: 20 tests
"""

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))

from ai.vision.quality_monitor import VisionQualityMonitor
from ai.vision.vision_pipeline import VisionPipeline


def _sample_image_bytes(size: int = 32) -> bytes:
    """Generate a simple PNG image for testing."""
    img = Image.fromarray(
        np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def pipeline():
    return VisionPipeline()


@pytest.fixture
def monitor():
    return VisionQualityMonitor(max_history=100)


class TestVisionPipelineProcess:
    """P31 T1-T5: Core pipeline processing tests (5 tests)."""

    def test_process_returns_all_fields(self, pipeline):
        """T1: process() returns feature_vector, latent, decoded_image, ssim, psnr."""
        data = _sample_image_bytes()
        result = pipeline.process(data)
        assert "error" not in result or result["error"] is None, result.get("error")
        assert "feature_vector" in result
        assert len(result["feature_vector"]) == 256  # VISION_DIM
        assert "latent" in result
        assert len(result["latent"]) == 64  # LATENT_DIM
        assert "decoded_image" in result
        assert "ssim" in result
        assert result["ssim"] >= -0.02  # Allow negligible floating-point error
        assert result["ssim"] <= 1.0
        assert "psnr" in result
        assert "time_ms" in result
        assert "image_hash" in result

    def test_process_different_images_give_different_latents(self, pipeline):
        """T2: Different images produce different latent vectors."""
        img1 = _sample_image_bytes(32)
        img2 = _sample_image_bytes(64)  # Different size = different content
        r1 = pipeline.process(img1)
        r2 = pipeline.process(img2)
        assert r1["latent"] != r2["latent"]

    def test_process_caches_identical_images(self, pipeline):
        """T3: Same image returns cached result on second call."""
        data = _sample_image_bytes()
        r1 = pipeline.process(data)
        assert not r1.get("cache_hit", False)
        r2 = pipeline.process(data)
        assert r2.get("cache_hit", False)

    def test_process_empty_data_returns_error(self, pipeline):
        """T4: Empty image data returns gracefully."""
        result = pipeline.process(b"")
        assert "error" in result

    def test_process_invalid_data_returns_error(self, pipeline):
        """T4b: Invalid image data returns gracefully."""
        result = pipeline.process(b"not_an_image")
        assert "error" in result


class TestVisionPipelineUtility:
    """P31 T6-T9: Utility method tests (4 tests)."""

    def test_encode_only_returns_vector(self, pipeline):
        """T6: encode_only returns 256-dim feature vector."""
        data = _sample_image_bytes()
        vec = pipeline.encode_only(data)
        assert len(vec) == 256

    def test_decode_latent_to_pil_returns_image(self, pipeline):
        """T7: decode_latent_to_pil returns PIL Image."""
        data = _sample_image_bytes()
        result = pipeline.process(data)
        latent = np.array(result["latent"], dtype=np.float32)
        pil = pipeline.decode_latent_to_pil(latent)
        assert isinstance(pil, Image.Image)
        assert pil.size == (128, 128)

    def test_get_latent_returns_64_dim(self, pipeline):
        """T8: get_latent returns 64-dim latent."""
        data = _sample_image_bytes()
        latent = pipeline.get_latent(data)
        assert len(latent) == 64

    def test_batch_process_returns_list(self, pipeline):
        """T9: batch_process returns list of results."""
        imgs = [_sample_image_bytes() for _ in range(3)]
        results = pipeline.batch_process(imgs)
        assert len(results) == 3
        for r in results:
            assert "feature_vector" in r


class TestVisionPipelineCache:
    """P31 T10-T12: Cache tests (3 tests)."""

    def test_cache_size_starts_at_zero(self, pipeline):
        """T10: Cache starts empty."""
        assert pipeline.cache_size() == 0

    def test_cache_size_increases_after_process(self, pipeline):
        """T11: Cache grows after processing images."""
        pipeline.process(_sample_image_bytes())
        assert pipeline.cache_size() == 1

    def test_clear_cache_empties(self, pipeline):
        """T12: Clear cache resets to zero."""
        pipeline.process(_sample_image_bytes())
        pipeline.clear_cache()
        assert pipeline.cache_size() == 0


class TestVisionPipelineStats:
    """P31 T13-T14: Stats and SSIM tests (2 tests)."""

    def test_get_stats_returns_fields(self, pipeline):
        """T13: get_stats returns all fields."""
        stats = pipeline.get_stats()
        assert "cache_size" in stats
        assert "input_size" in stats
        assert "vision_dim" in stats
        assert "latent_dim" in stats
        assert stats["input_size"] == 128
        assert stats["vision_dim"] == 256
        assert stats["latent_dim"] == 64

    def test_ssim_same_image_is_one(self, pipeline):
        """T14: SSIM of image with itself equals 1.0."""
        arr = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8).astype(np.float32)
        ssim = pipeline._compute_ssim(arr, arr.copy())
        assert abs(ssim - 1.0) < 0.01


class TestVisionQualityMonitor:
    """P31 T15-T18: QualityMonitor tests (4 tests)."""

    def test_report_empty_returns_zeros(self, monitor):
        """T15: Empty report returns zero metrics."""
        report = monitor.report()
        assert report["total_calls"] == 0
        assert report["avg_ssim"] == 0.0

    def test_report_after_records(self, monitor):
        """T16: Report returns correct averages after recording."""
        for _ in range(10):
            monitor.record({
                "ssim": 0.8,
                "psnr": 25.0,
                "time_ms": 50.0,
                "original_size": (128, 128),
                "cache_hit": False,
                "image_hash": "abc",
            })
        report = monitor.report()
        assert report["total_calls"] == 10
        assert abs(report["avg_ssim"] - 0.8) < 0.01
        assert abs(report["avg_psnr"] - 25.0) < 0.1

    def test_quality_trend_insufficient(self, monitor):
        """T17: Trend with < 4 records returns insufficient_data."""
        trend = monitor.quality_trend()
        assert trend["assessment"] == "insufficient_data"

    def test_quality_trend_stable(self, monitor):
        """T18: Trend with stable data returns stable."""
        for _ in range(20):
            monitor.record({
                "ssim": 0.8,
                "psnr": 25.0,
                "time_ms": 50.0,
                "original_size": (128, 128),
                "cache_hit": False,
                "image_hash": "abc",
            })
        trend = monitor.quality_trend(window=10)
        assert trend["assessment"] in ("stable", "improving")


class TestVisionServiceExtension:
    """P31 T19-T20: VisionService extension tests (2 tests)."""

    async def test_encode_with_pipeline_returns_full_result(self):
        """T19: encode_with_pipeline returns vision pipeline result."""
        from services.vision_service import VisionService
        svc = VisionService()
        data = _sample_image_bytes()
        result = await svc.encode_with_pipeline(data)
        assert "error" not in result or result.get("error") is None
        assert "feature_vector" in result
        assert "latent" in result
        assert "ssim" in result

    async def test_batch_encode_returns_list(self):
        """T20: batch_encode returns list of results."""
        from services.vision_service import VisionService
        svc = VisionService()
        imgs = [_sample_image_bytes() for _ in range(3)]
        results = await svc.batch_encode(imgs)
        assert len(results) == 3
        for r in results:
            assert "feature_vector" in r or "error" in r
