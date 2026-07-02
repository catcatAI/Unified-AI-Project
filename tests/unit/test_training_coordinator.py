"""Tests for ai.core.training_coordinator"""
import pytest


class TestTrainingCoordinator:
    def test_import(self):
        from ai.core.training_coordinator import DomainTrainingRecord, TrainingCoordinator
        assert TrainingCoordinator is not None
        assert DomainTrainingRecord is not None

    def test_instantiation(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        assert tc._domain_map == {}
        assert tc._seen_hashes == {}
        assert tc.bus is None
        assert tc._max_examples == 100
        assert tc._max_hashes == 10000

    @pytest.mark.asyncio
    async def test_assign_domain_no_bus(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        assert await tc.assign_domain("math") == "ed3n"
        assert await tc.assign_domain("knowledge") == "garden"
        assert await tc.assign_domain("creative") == "cloud"
        assert await tc.assign_domain("reflex") == "ed3n"
        assert await tc.assign_domain("nonexistent") is None

    @pytest.mark.asyncio
    async def test_assign_domain_unknown(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        assert await tc.assign_domain("unknown") == "garden"

    @pytest.mark.asyncio
    async def test_record_training_creates_new_entry(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        await tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        assert "math" in tc._domain_map
        assert tc._domain_map["math"].trained_count == 5
        assert tc._domain_map["math"].accuracy == 0.95

    @pytest.mark.asyncio
    async def test_record_training_updates_existing_entry(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        await tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        await tc.record_training("math", "ed3n-v1", 3, 0.97, [{"input": "2+2=?"}])
        assert tc._domain_map["math"].trained_count == 8
        assert tc._domain_map["math"].accuracy == 0.97

    @pytest.mark.asyncio
    async def test_should_skip_duplicate_input(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        await tc.record_training("math", "ed3n-v1", 1, 0.9, [{"input": "1+1=?"}])
        assert await tc.should_skip("math", "1+1=?") is True
        assert await tc.should_skip("math", "2+2=?") is False
        assert await tc.should_skip("knowledge", "1+1=?") is False

    @pytest.mark.asyncio
    async def test_get_domain_report_empty(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        report = await tc.get_domain_report()
        assert "No training records yet" in report

    @pytest.mark.asyncio
    async def test_get_domain_report_with_data(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        await tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        report = await tc.get_domain_report()
        assert "math" in report
        assert "ed3n-v1" in report
        assert "5" in report

    @pytest.mark.asyncio
    async def test_deconflict_samples(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        samples = [
            {"domain": "math", "input": "1+1"},
            {"domain": "knowledge", "input": "what is AI"},
            {"domain": "creative", "input": "poem"},
            {"domain": "reflex", "input": "ok"},
        ]
        batches = await tc.deconflict_samples(samples)
        assert "ed3n" in batches
        assert "garden" in batches
        assert "cloud" in batches
        assert len(batches["ed3n"]) == 2
        assert len(batches["garden"]) == 1

    @pytest.mark.asyncio
    async def test_sync_reflex_patterns_no_method(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator()
        source = object()
        target = object()
        result = await tc.sync_reflex_patterns(source, target)
        assert result == 0

    @pytest.mark.asyncio
    async def test_max_examples_eviction(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator(max_examples_per_domain=3)
        for i in range(10):
            await tc.record_training("test", "model-v1", 1, 0.9, [{"input": f"sample_{i}"}])
        assert len(tc._domain_map["test"].examples) == 3
        assert tc._domain_map["test"].examples[-1]["input"] == "sample_9"

    @pytest.mark.asyncio
    async def test_max_hashes_eviction(self):
        from ai.core.training_coordinator import TrainingCoordinator
        tc = TrainingCoordinator(max_hashes_per_domain=5)
        for i in range(10):
            await tc.record_training("test", "model-v1", 1, 0.9, [{"input": f"sample_{i}"}])
        assert len(tc._seen_hashes["test"]) <= 5