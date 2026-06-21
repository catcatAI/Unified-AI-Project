"""
Tests for P37 production hardening:
  - MultimodalErrorRecovery (retry, fallback, checkpoint, crisis_log)
  - MultimodalStatePersistence (save, load, list, prune)
  - MultimodalQualityMonitor (background sampling, degradation, alerts)
  - Health endpoint enhancement

Total: 15 tests.
"""

import asyncio
import json
import os
import tempfile
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.multimodal_error_recovery import MultimodalErrorRecovery, _write_crisis_log
from services.multimodal_state_persistence import MultimodalStatePersistence
from services.multimodal_quality_monitor import MultimodalQualityMonitor


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_service():
    """Create a mock service with async encode/decode/train methods.

    Note: does NOT mock _get_cml to avoid state_persistence
    trying to serialize MagicMock objects (which causes infinite loops).
    """
    svc = MagicMock()
    svc.encode = AsyncMock(return_value={"item_id": "test_001", "latent": [0.1, 0.2]})
    svc.decode = AsyncMock(return_value={"decoded": "data:image/png;base64,test"})
    svc.train = AsyncMock(return_value={"status": "completed", "mode": "full"})
    svc.save_weights = AsyncMock(return_value={"status": "saved", "path": "/tmp/test.npz"})
    svc.load_weights = AsyncMock(return_value={"status": "loaded"})
    svc.list_items = AsyncMock(return_value={"items": {"a": {"modality": "vision"}}, "count": 1})
    svc.get_item = AsyncMock(return_value={
        "modality": "vision", "latent": [0.1, 0.2], "feature_vector": [0.3, 0.4],
    })
    svc.evaluate = AsyncMock(return_value={
        "metrics": {"ssim": 0.85, "snr": 15.0},
    })
    # Explicitly avoid _get_cml mocking (state_persistence checks isinstance)
    # to prevent MagicMock recursive serialization hangs.
    svc._get_cml = None  # type: ignore
    return svc


@pytest.fixture
def error_recovery(mock_service):
    return MultimodalErrorRecovery(mock_service)


@pytest.fixture
def state_persistence(mock_service, tmp_path):
    cp_dir = str(tmp_path / "checkpoints")
    return MultimodalStatePersistence(mock_service, checkpoint_dir=cp_dir)


@pytest.fixture
def quality_monitor(mock_service):
    return MultimodalQualityMonitor(mock_service, interval_sec=0.1)


# =============================================================================
# MultimodalErrorRecovery Tests
# =============================================================================


class TestErrorRecoveryEncode:
    """Tests for encode_with_retry."""

    @pytest.mark.asyncio
    async def test_encode_success_first_try(self, error_recovery, mock_service):
        """Success on first attempt returns result with recovery info."""
        result = await error_recovery.encode_with_retry(b"test_data", "vision")
        assert result.get("item_id") == "test_001"
        assert result["recovery"]["attempts"] == 1
        assert result["recovery"]["retried"] is False

    @pytest.mark.asyncio
    async def test_encode_retry_on_failure(self, error_recovery, mock_service):
        """Retry on failure returns result after retry."""
        mock_service.encode.side_effect = [
            {"error": "First failure"},
            {"item_id": "test_002", "latent": [0.3, 0.4]},
        ]
        result = await error_recovery.encode_with_retry(b"test_data", "vision")
        assert result.get("item_id") == "test_002"
        assert result["recovery"]["retried"] is True
        assert result["recovery"]["attempts"] == 2

    @pytest.mark.asyncio
    async def test_encode_all_retries_fail(self, error_recovery, mock_service):
        """All retries fail returns error dict."""
        mock_service.encode.side_effect = [
            {"error": "err1"}, {"error": "err2"}, {"error": "err3"}, {"error": "err4"},
        ]
        result = await error_recovery.encode_with_retry(b"test_data", "vision", max_retries=3)
        assert "error" in result
        assert result["recovery"]["failed"] is True
        assert result["recovery"]["attempts"] == 4


class TestErrorRecoveryDecode:
    """Tests for decode_with_fallback."""

    @pytest.mark.asyncio
    async def test_decode_success(self, error_recovery, mock_service):
        """Success returns result without fallback."""
        result = await error_recovery.decode_with_fallback("test_001", "vision")
        assert result["recovery"]["fallback_used"] is False
        assert "decoded" in result

    @pytest.mark.asyncio
    async def test_decode_fallback_on_error(self, error_recovery, mock_service):
        """Failure returns text fallback description."""
        mock_service.decode.side_effect = RuntimeError("Decoder crashed")
        result = await error_recovery.decode_with_fallback("test_001", "vision")
        assert result["recovery"]["fallback_used"] is True
        assert "fallback_description" in result

    @pytest.mark.asyncio
    async def test_decode_fallback_no_item(self, error_recovery, mock_service):
        """Failure with no item returns not-found fallback."""
        mock_service.decode.side_effect = RuntimeError("Not found")
        mock_service.get_item.return_value = None
        result = await error_recovery.decode_with_fallback("unknown", "audio")
        assert result["recovery"]["fallback_used"] is True
        assert "not found" in result.get("fallback_description", "").lower()


class TestErrorRecoveryTrain:
    """Tests for train_with_checkpoint."""

    @pytest.mark.asyncio
    async def test_train_with_checkpoint(self, error_recovery, mock_service):
        """Training with checkpoint returns checkpoint info."""
        result = await error_recovery.train_with_checkpoint(
            mode="full", epochs=2, checkpoint_label="test_cp"
        )
        assert result.get("status") == "completed"
        assert "checkpoint" in result
        assert result["checkpoint"]["saved_before_training"] is True

    @pytest.mark.asyncio
    async def test_train_checkpoint_on_failure(self, error_recovery, mock_service):
        """Failed training returns checkpoint info for resumability."""
        mock_service.train.side_effect = RuntimeError("Training failed")
        result = await error_recovery.train_with_checkpoint(
            mode="contrastive", epochs=2, checkpoint_label="fail_cp"
        )
        assert result.get("status") == "error"
        assert result["checkpoint"]["resumable"] is True
        assert result["checkpoint"]["saved_before_training"] is True


class TestErrorRecoveryState:
    """Tests for recovery state management."""

    def test_recovery_state_initial(self, error_recovery):
        """Initial recovery state has empty counters."""
        state = error_recovery.get_recovery_state()
        assert state["retry_counts"] == {}
        assert state["crisis_levels"] == {}
        assert state["checkpoint_dir"] is not None

    def test_reset_counters(self, error_recovery):
        """reset_counters clears all counters."""
        error_recovery._retry_count["test"] = 5
        error_recovery.reset_counters()
        assert error_recovery._retry_count == {}

    @pytest.mark.asyncio
    async def test_crisis_log_write(self, error_recovery, tmp_path):
        """_write_crisis_log appends to crisis_log.txt."""
        log_path = str(tmp_path / "crisis_log.txt")
        with patch("services.multimodal_error_recovery.CRISIS_LOG_PATH", log_path):
            _write_crisis_log(3, {"test": True})
            with open(log_path, "r") as f:
                content = f.read()
            assert "CRISIS_LOG" in content
            assert "Level 3" in content


# =============================================================================
# MultimodalStatePersistence Tests
# =============================================================================


class TestStatePersistence:
    """Tests for MultimodalStatePersistence."""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, state_persistence):
        """save_checkpoint creates checkpoint with metadata."""
        result = await state_persistence.save_checkpoint("test_cp_001")
        assert result["status"] == "saved"
        assert result["label"] == "test_cp_001"
        assert os.path.isdir(result["path"])
        # Check metadata was written
        meta_path = os.path.join(result["path"], "metadata.json")
        assert os.path.exists(meta_path)

    @pytest.mark.asyncio
    async def test_save_checkpoint_auto_label(self, state_persistence):
        """save_checkpoint generates a label if not provided."""
        result = await state_persistence.save_checkpoint()
        assert result["status"] == "saved"
        assert result["label"].startswith("cp_")

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, state_persistence):
        """list_checkpoints returns saved checkpoints."""
        await state_persistence.save_checkpoint("cp_a")
        await state_persistence.save_checkpoint("cp_b")
        result = await state_persistence.list_checkpoints()
        assert result["count"] >= 2
        assert len(result["checkpoints"]) >= 2

    @pytest.mark.asyncio
    async def test_load_checkpoint_not_found(self, state_persistence):
        """load_checkpoint returns error for unknown label."""
        result = await state_persistence.load_checkpoint("nonexistent")
        assert result["status"] == "error"
        assert "not found" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_prune_checkpoints(self, state_persistence):
        """prune_checkpoints removes old checkpoints."""
        for i in range(5):
            await state_persistence.save_checkpoint(f"cp_{i:03d}")
        removed = await state_persistence.prune_checkpoints(keep=2)
        assert removed >= 3
        remaining = await state_persistence.list_checkpoints()
        assert remaining["count"] <= 2

    @pytest.mark.asyncio
    async def test_get_checkpoint_path(self, state_persistence):
        """get_checkpoint_path returns path for existing checkpoint."""
        await state_persistence.save_checkpoint("path_test")
        path = state_persistence.get_checkpoint_path("path_test")
        assert path is not None
        assert os.path.isdir(path)
        # Non-existent returns None
        assert state_persistence.get_checkpoint_path("no_such_cp") is None


# =============================================================================
# MultimodalQualityMonitor Tests
# =============================================================================


class TestQualityMonitor:
    """Tests for MultimodalQualityMonitor."""

    @pytest.mark.asyncio
    async def test_start_stop(self, quality_monitor):
        """start() and stop() lifecycle works."""
        assert quality_monitor.is_running is False
        await quality_monitor.start()
        assert quality_monitor.is_running is True
        await quality_monitor.stop()
        assert quality_monitor.is_running is False

    @pytest.mark.asyncio
    async def test_report_no_data(self, quality_monitor):
        """report() returns no_data status when no samples taken."""
        report = quality_monitor.report()
        assert report["status"] == "no_data"
        assert report["total_samples"] == 0

    @pytest.mark.asyncio
    async def test_sample_then_report(self, quality_monitor, mock_service):
        """After sampling, report returns quality metrics."""
        await quality_monitor._sample_quality()
        report = quality_monitor.report()
        assert report["total_samples"] == 1
        assert "last_vision_quality" in report
        assert "last_audio_quality" in report

    @pytest.mark.asyncio
    async def test_degradation_detection(self, quality_monitor, mock_service):
        """Degradation is detected when quality drops > 10%."""
        # Populate history with 3 high quality samples (need >=3 for baseline)
        for _ in range(3):
            quality_monitor._history.append({
                "timestamp": time.time(),
                "vision": {"quality": 0.95, "source": "synthetic"},
                "audio": {"quality": 20.0, "source": "synthetic"},
            })
        # Test with low quality — should detect degradation
        degradation = quality_monitor._detect_degradation(0.5, 5.0)
        assert degradation is not None
        # Check which modality degraded
        assert "vision" in degradation

    @pytest.mark.asyncio
    async def test_no_false_degradation(self, quality_monitor):
        """Similar quality does not trigger false degradation."""
        quality_monitor._history.append({
            "timestamp": time.time(),
            "vision": {"quality": 0.85, "source": "synthetic"},
            "audio": {"quality": 15.0, "source": "synthetic"},
        })
        quality_monitor._history.append({
            "timestamp": time.time(),
            "vision": {"quality": 0.84, "source": "synthetic"},
            "audio": {"quality": 14.8, "source": "synthetic"},
        })
        degradation = quality_monitor._detect_degradation(0.83, 14.5)
        assert degradation is None

    @pytest.mark.asyncio
    async def test_quality_trend_insufficient(self, quality_monitor):
        """quality_trend returns insufficient_data with < 4 samples."""
        quality_monitor._history.append({"timestamp": time.time()})
        trend = quality_monitor.quality_trend()
        assert trend["status"] == "insufficient_data"
