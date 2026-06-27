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

    def test_assign_domain_no_bus(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        assert tc.assign_domain("math") == "ed3n"
        assert tc.assign_domain("knowledge") == "garden"
        assert tc.assign_domain("creative") == "cloud"
        assert tc.assign_domain("reflex") == "ed3n"
        assert tc.assign_domain("nonexistent") is None

    def test_assign_domain_unknown(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        assert tc.assign_domain("unknown") == "garden"

    def test_record_training_creates_new_entry(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        assert "math" in tc._domain_map
        assert tc._domain_map["math"].trained_count == 5
        assert tc._domain_map["math"].accuracy == 0.95

    def test_record_training_updates_existing_entry(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        tc.record_training("math", "ed3n-v1", 3, 0.97, [{"input": "2+2=?"}])
        assert tc._domain_map["math"].trained_count == 8
        assert tc._domain_map["math"].accuracy == 0.97

    def test_should_skip_duplicate_input(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.record_training("math", "ed3n-v1", 1, 0.9, [{"input": "1+1=?"}])
        assert tc.should_skip("math", "1+1=?") is True
        assert tc.should_skip("math", "2+2=?") is False
        assert tc.should_skip("knowledge", "1+1=?") is False

    def test_get_domain_report_empty(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        report = tc.get_domain_report()
        assert "No training records yet" in report

    def test_get_domain_report_with_data(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.record_training("math", "ed3n-v1", 5, 0.95, [{"input": "1+1=?"}])
        report = tc.get_domain_report()
        assert "math" in report
        assert "ed3n-v1" in report
        assert "5" in report

    def test_deconflict_samples(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        samples = [
            {"domain": "math", "input": "1+1"},
            {"domain": "knowledge", "input": "what is AI"},
            {"domain": "creative", "input": "poem"},
            {"domain": "reflex", "input": "ok"},
        ]
        batches = tc.deconflict_samples(samples)
        assert "ed3n" in batches
        assert "garden" in batches
        assert "cloud" in batches
        assert len(batches["ed3n"]) == 2
        assert len(batches["garden"]) == 1

    def test_sync_reflex_patterns_no_method(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        source = object()
        target = object()
        result = tc.sync_reflex_patterns(source, target)
        assert result == 0
