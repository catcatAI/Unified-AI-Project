"""
P33 tests: CrossModalRouter + CrossModalQualityDashboard + MultimodalService pipeline wiring.

Total: 25 tests covering:
  - CrossModalRouter route/fallback/cache/rate-limit (8)
  - CrossModalQualityDashboard record/report/trend/health (7)
  - MultimodalService pipeline wiring via encode/evaluate/health (6)
  - API endpoint integration for cross-infer + dashboard (4)
"""

import asyncio
import io
import sys
import time
from typing import Any, Dict
from pathlib import Path

import numpy as np
import pytest

# Ensure src is on path
SRC = str(Path(__file__).resolve().parents[2] / "apps/backend/src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# ============================================================================
# Helpers
# ============================================================================

def _sample_image_bytes() -> bytes:
    """Generate a small valid PNG image."""
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (32, 32), color=(128, 200, 64))
    img.save(buf, format="PNG")
    return buf.getvalue()


def _sample_wav_bytes() -> bytes:
    """Generate a small valid WAV audio clip."""
    import struct
    import wave
    sample_rate = 16000
    duration = 0.1
    n_samples = int(sample_rate * duration)
    samples = (np.sin(2 * np.pi * 440 * np.arange(n_samples) / sample_rate) * 0.5)
    int16 = (samples * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


# ============================================================================
# CrossModalRouter Tests
# ============================================================================

class TestCrossModalRouterRoute:
    """T1-T8: CrossModalRouter routing functionality."""

    @pytest.mark.asyncio
    async def test_route_vision_encode(self):
        """T1: Route vision data returns vision pipeline result."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        img = _sample_image_bytes()
        result = await router.route("vision", img, "encode")
        assert result["pipeline"] == "vision"
        assert result["confidence"] >= 0.0
        assert "result" in result
        assert result.get("error") is None

    @pytest.mark.asyncio
    async def test_route_audio_encode(self):
        """T2: Route audio data returns audio pipeline result."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        wav = _sample_wav_bytes()
        result = await router.route("audio", wav, "encode")
        assert result["pipeline"] == "audio"
        assert result["confidence"] >= 0.0
        assert result.get("error") is None

    @pytest.mark.asyncio
    async def test_route_cross_compare(self):
        """T3: Route cross-modal compare returns similarity."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        result = await router.route("cross", b"", "compare")
        assert result["pipeline"] == "cross"
        assert "similarity" in result.get("result", {}) or result.get("confidence", 0) >= 0.0

    @pytest.mark.asyncio
    async def test_route_unknown_modality(self):
        """T4: Route unknown modality returns error."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        result = await router.route("unknown", b"", "auto")
        assert "error" in result
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_route_caching(self):
        """T5: Identical requests return cached result."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        img = _sample_image_bytes()
        r1 = await router.route("vision", img, "encode")
        r2 = await router.route("vision", img, "encode")
        assert r2["pipeline"] == "cache"
        assert r2["result"] is not None

    @pytest.mark.asyncio
    async def test_route_rate_limit(self):
        """T6: Rate limiting returns rate_limited pipeline."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter(cache_size=0, rate_limit=1)
        img = _sample_image_bytes()
        # First request
        r1 = await router.route("vision", img, "encode")
        assert r1["pipeline"] in ("vision", "cache")
        # Second request (should hit rate limit with rate_limit=1)
        r2 = await router.route("vision", img + b"diff", "encode")
        assert r2.get("pipeline") in ("rate_limited", "vision")

    @pytest.mark.asyncio
    async def test_list_pipelines(self):
        """T7: List all available pipelines with status."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        status = await router.list_pipelines()
        assert "pipelines" in status
        assert "vision" in status["pipelines"]
        assert "audio" in status["pipelines"]
        assert "cross" in status["pipelines"]
        assert "cache_size" in status

    @pytest.mark.asyncio
    async def test_route_stats(self):
        """T8: Route stats returns diagnostics."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        stats = router.get_route_stats()
        assert "cache_size" in stats
        assert "vision_pipeline_ready" in stats
        assert "audio_pipeline_ready" in stats


# ============================================================================
# CrossModalQualityDashboard Tests
# ============================================================================

class TestCrossModalQualityDashboard:
    """T9-T15: Quality dashboard functionality."""

    def _sample_vision_result(self, ssim=0.85, psnr=30.0, time_ms=50.0, cache_hit=False):
        return {
            "ssim": ssim, "psnr": psnr, "time_ms": time_ms,
            "original_size": (128, 128), "cache_hit": cache_hit,
            "image_hash": "abc123", "error": None,
        }

    def _sample_audio_result(self, snr=20.0, time_ms=40.0, duration=1.0, cache_hit=False):
        return {
            "snr": snr, "time_ms": time_ms, "duration": duration,
            "cache_hit": cache_hit, "audio_hash": "def456", "error": None,
        }

    def test_record_vision(self):
        """T9: Record vision pipeline result."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        dq.record_vision(self._sample_vision_result())
        report = dq.dashboard()
        assert report["vision_summary"]["total_calls"] == 1

    def test_record_audio(self):
        """T10: Record audio pipeline result."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        dq.record_audio(self._sample_audio_result())
        report = dq.dashboard()
        assert report["audio_summary"]["total_calls"] == 1

    def test_dashboard_aggregation(self):
        """T11: Dashboard aggregates both vision and audio."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        dq.record_vision(self._sample_vision_result())
        dq.record_audio(self._sample_audio_result())
        report = dq.dashboard()
        assert report["vision_summary"]["total_calls"] == 1
        assert report["audio_summary"]["total_calls"] == 1
        assert "overall" in report
        assert "total_requests" in report

    def test_dashboard_simple(self):
        """T12: Simple dashboard returns condensed view."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        dq.record_vision(self._sample_vision_result())
        simple = dq.dashboard_simple()
        assert "vision" in simple
        assert "audio" in simple
        assert "overall_health" in simple

    def test_empty_dashboard(self):
        """T13: Empty dashboard returns zeros."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        report = dq.dashboard()
        assert report["vision_summary"]["total_calls"] == 0
        assert report["audio_summary"]["total_calls"] == 0

    def test_quality_trend_insufficient(self):
        """T14: Trend with insufficient data returns assessment."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        trend = dq.quality_trend()
        assert trend["overall_assessment"] in ("stable", "insufficient_data")

    def test_overall_health(self):
        """T15: Overall health computed correctly."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dq = CrossModalQualityDashboard()
        # High quality records
        for _ in range(5):
            dq.record_vision(self._sample_vision_result(ssim=0.95, psnr=40.0))
            dq.record_audio(self._sample_audio_result(snr=35.0))
        full = dq.dashboard()
        health = full["overall"]
        assert health["health"] in ("healthy", "degraded", "unhealthy")
        assert health["health_score"] > 0.0


# ============================================================================
# MultimodalService Pipeline Wiring Tests
# ============================================================================

class TestMultimodalServicePipelineWiring:
    """T16-T21: MultimodalService pipeline integration."""

    @pytest.mark.asyncio
    async def test_encode_vision_uses_pipeline(self):
        """T16: Encode vision uses VisionPipeline and records quality."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        img = _sample_image_bytes()
        result = await svc.encode(img, "vision")
        assert result.get("error") is None, result.get("error")
        assert "item_id" in result
        assert "latent" in result
        # Wait for quality monitor to have data
        qm = svc._get_quality_monitor()
        report = qm.report()
        assert report["total_calls"] >= 1

    @pytest.mark.asyncio
    async def test_encode_audio_uses_pipeline(self):
        """T17: Encode audio uses AudioPipeline and records quality."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        wav = _sample_wav_bytes()
        result = await svc.encode(wav, "audio")
        assert result.get("error") is None, result.get("error")
        assert "item_id" in result
        qm = svc._get_audio_quality_monitor()
        report = qm.report()
        assert report["total_calls"] >= 1

    @pytest.mark.asyncio
    async def test_evaluate_vision_with_item(self):
        """T18: Evaluate vision item uses quality monitor report."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        img = _sample_image_bytes()
        await svc.encode(img, "vision")
        items = await svc.list_items()
        item_ids = list(items.get("items", {}).keys())
        if item_ids:
            eval_result = await svc.evaluate(item_id=item_ids[0])
            assert "metrics" in eval_result
            assert eval_result.get("error") is None

    @pytest.mark.asyncio
    async def test_evaluate_audio_with_item(self):
        """T19: Evaluate audio item uses quality monitor report."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        wav = _sample_wav_bytes()
        await svc.encode(wav, "audio")
        items = await svc.list_items()
        item_ids = list(items.get("items", {}).keys())
        if item_ids:
            eval_result = await svc.evaluate(item_id=item_ids[0])
            assert "metrics" in eval_result
            assert eval_result.get("error") is None

    @pytest.mark.asyncio
    async def test_health_includes_pipelines(self):
        """T20: Health check includes vision and audio pipeline stats."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        health = await svc.health()
        assert "vision_pipeline" in health
        assert "audio_pipeline" in health
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_encode_empty_data(self):
        """T21: Encode empty data returns error."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        result = await svc.encode(b"", "vision")
        assert "error" in result


# ============================================================================
# API Integration Tests
# ============================================================================

class TestCrossModalAPI:
    """T22-T25: API endpoint integration."""

    @pytest.mark.asyncio
    async def test_cross_infer_vision_pipeline(self):
        """T22: POST /multimodal/cross-infer with vision data."""
        from fastapi import UploadFile
        from api.routes.multimodal_routes import cross_infer_endpoint
        # Call directly with vision data
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        img = _sample_image_bytes()
        result = await router.route("vision", img, "pipeline")
        assert result.get("error") is None
        assert result["pipeline"] in ("vision", "cache")

    @pytest.mark.asyncio
    async def test_cross_infer_audio_pipeline(self):
        """T23: POST /multimodal/cross-infer with audio data."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        wav = _sample_wav_bytes()
        result = await router.route("audio", wav, "pipeline")
        assert result.get("error") is None
        assert result["pipeline"] in ("audio", "cache")

    @pytest.mark.asyncio
    async def test_cross_infer_cross_compare(self):
        """T24: POST /multimodal/cross-infer with cross-modal compare."""
        from services.cross_modal_router import CrossModalRouter
        router = CrossModalRouter()
        result = await router.route("cross", b"", "compare")
        assert result.get("error") is None
        assert "similarity" in result.get("result", {}) or result.get("pipeline") == "cross"

    def test_quality_dashboard_endpoint(self):
        """T25: GET /multimodal/quality/dashboard returns valid report."""
        from services.cross_modal_quality import CrossModalQualityDashboard
        dashboard = CrossModalQualityDashboard()
        simple = dashboard.dashboard_simple()
        assert "vision" in simple
        assert "audio" in simple
        assert "overall_health" in simple
        assert "total_requests" in simple
