"""
P36 tests: ContinuousMultimodalLearning + MultimodalMemoryStore.

Total: 20 tests covering:
  - ContinuousMultimodalLearning: record/auto-train/trend/stats (10)
  - MultimodalMemoryStore: store/search/recall/compaction/stats (10)
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

SRC = str(Path(__file__).resolve().parents[2] / "apps/backend/src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# ============================================================================
# ContinuousMultimodalLearning Tests
# ============================================================================

class TestContinuousMultimodalLearning:
    """T1-T10: CML functionality."""

    def test_record_encode_adds_to_buffer(self):
        """T1: record_encode adds an example to the buffer."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=64)
        assert cml.get_stats()["buffer_size"] == 0
        cml.record_encode("vision", [0.1] * 256, [0.2] * 64, 0.8)
        assert cml.get_stats()["buffer_size"] == 1

    def test_record_encode_multiple_modalities(self):
        """T2: CML handles both vision and audio modality records."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=64)
        cml.record_encode("vision", [0.1] * 256, [0.2] * 64, 0.8)
        cml.record_encode("audio", [0.3] * 128, [0.4] * 64, 15.0)
        assert cml.get_stats()["buffer_size"] == 2

    def test_buffer_max_respected(self):
        """T3: Buffer does not exceed max capacity."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=10)
        for i in range(20):
            cml.record_encode("vision", [float(i)] * 256, [float(i)] * 64, 0.5)
        assert cml.get_stats()["buffer_size"] == 10
        assert cml.get_stats()["total_encodes"] == 20

    def test_should_train_false_when_buffer_small(self):
        """T4: should_train returns False when buffer below threshold."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(auto_train_threshold=10)
        assert cml.should_train() is False
        for i in range(5):
            cml.record_encode("vision", [0.1] * 256, [0.2] * 64, 0.5)
        assert cml.should_train() is False

    def test_should_train_true_when_ready(self):
        """T5: should_train returns True when buffer >= threshold and time passed."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(auto_train_threshold=5, min_interval_sec=0)
        for i in range(5):
            cml.record_encode("vision", [float(i)] * 256, [float(i)] * 64, 0.5)
        assert cml.should_train() is True

    def test_micro_train_runs_successfully(self):
        """T6: micro_train completes without errors."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=32, auto_train_threshold=10)
        for i in range(10):
            cml.record_encode("vision", [float(i)] * 256, [float(i)] * 64, 0.5)
        result = cml.micro_train(epochs=2)
        assert result["status"] in ("completed", "skipped")
        if result["status"] == "completed":
            assert result["training_runs_total"] >= 1
            assert "time_ms" in result

    def test_micro_train_auto_trim(self):
        """T7: micro_train trims buffer after completion."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=32, auto_train_threshold=5, min_interval_sec=0)
        for i in range(8):
            cml.record_encode("vision", [float(i)] * 256, [float(i)] * 64, 0.5)
        result = cml.micro_train(epochs=2)
        if result["status"] == "completed":
            # Buffer should be trimmed to ~25% of original (8/4=2)
            assert cml.get_stats()["buffer_size"] <= 5

    def test_quality_trend_insufficient(self):
        """T8: quality_trend returns insufficient_data when no history."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning()
        trend = cml.quality_trend()
        assert trend["delta_assessment"] == "insufficient_data"

    def test_quality_trend_with_data(self):
        """T9: quality_trend returns assessment after recording quality."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning()
        for i in range(10):
            cml.record_quality({"delta": 0.01 * i, "loss_before": 1.0, "loss_after": 1.0 - 0.01 * i})
        trend = cml.quality_trend()
        assert trend["delta_assessment"] in ("improving", "stable")
        assert trend["total_training_runs"] >= 0

    def test_get_stats(self):
        """T10: get_stats returns all expected fields."""
        from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
        cml = ContinuousMultimodalLearning(buffer_max=64, auto_train_threshold=32)
        cml.record_encode("vision", [0.1] * 256, [0.2] * 64, 0.8)
        stats = cml.get_stats()
        assert stats["total_encodes"] == 1
        assert stats["buffer_size"] == 1
        assert stats["buffer_capacity"] == 64
        assert stats["auto_train_threshold"] == 32


# ============================================================================
# MultimodalMemoryStore Tests
# ============================================================================

class TestMultimodalMemoryStore:
    """T11-T20: Memory store functionality."""

    @pytest.mark.asyncio
    async def test_store_returns_entry_id(self):
        """T11: store() returns a unique entry ID."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        eid = await store.store("vision", [0.1] * 64, {"label": "test"})
        assert eid is not None
        assert eid.startswith("vision_")

    @pytest.mark.asyncio
    async def test_store_multiple_entries(self):
        """T12: store() handles multiple entries."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        eid1 = await store.store("vision", [0.1] * 64)
        eid2 = await store.store("audio", [0.2] * 64)
        assert eid1 != eid2
        assert await store.count() == 2

    @pytest.mark.asyncio
    async def test_search_returns_similar(self):
        """T13: search() returns similar latents ordered by score."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        await store.store("vision", [0.1] * 64, {"name": "a"})
        await store.store("vision", [0.2] * 64, {"name": "b"})
        await store.store("vision", [0.9] * 64, {"name": "c"})
        results = await store.search([0.85] * 64, top_k=3)
        assert len(results) >= 1
        # First result should be the most similar
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_with_modality_filter(self):
        """T14: search() respects modality_filter."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        await store.store("vision", [0.1] * 64)
        await store.store("audio", [0.1] * 64)
        results = await store.search([0.1] * 64, top_k=5, modality_filter="vision")
        assert all(r["modality"] == "vision" for r in results)

    @pytest.mark.asyncio
    async def test_recall_by_time(self):
        """T15: recall_by_time returns entries within time window."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        await store.store("vision", [0.1] * 64)
        results = await store.recall_by_time(hours=24)
        assert len(results) >= 1
        # Should be sorted by timestamp descending
        timestamps = [r["timestamp"] for r in results]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_recall_by_time_with_modality(self):
        """T16: recall_by_time respects modality_filter."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        await store.store("vision", [0.1] * 64)
        await store.store("audio", [0.2] * 64)
        results = await store.recall_by_time(hours=24, modality_filter="audio")
        assert all(r["modality"] == "audio" for r in results)

    @pytest.mark.asyncio
    async def test_get_entry(self):
        """T17: get_entry returns stored entry."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        eid = await store.store("vision", [0.1] * 64, {"label": "test"})
        entry = await store.get_entry(eid)
        assert entry is not None
        assert entry["modality"] == "vision"
        assert entry["metadata"]["label"] == "test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self):
        """T18: get_entry returns None for unknown ID."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        entry = await store.get_entry("nonexistent")
        assert entry is None

    @pytest.mark.asyncio
    async def test_stats(self):
        """T19: stats returns expected fields."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore()
        await store.store("vision", [0.1] * 64)
        await store.store("audio", [0.2] * 64)
        stats = await store.stats()
        assert stats["total_entries"] == 2
        assert stats["vision_entries"] == 1
        assert stats["audio_entries"] == 1

    @pytest.mark.asyncio
    async def test_compact_and_cleanup(self):
        """T20: compact() runs without errors."""
        from ai.multimodal.multimodal_memory import MultimodalMemoryStore
        store = MultimodalMemoryStore(ttl_days=0, ttl_compact_days=0)  # Expire immediately
        await store.store("vision", [0.1] * 64)
        result = await store.compact()
        assert "compacted" in result
        assert "deleted" in result
        assert "remaining" in result
