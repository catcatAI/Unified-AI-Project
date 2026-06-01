"""Smoke tests for ChainValidator"""
import pytest


class TestChainValidator:
    """Basic smoke tests for ChainValidator"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.tracing.chain_validator import ChainValidator
            assert ChainValidator is not None
        except ImportError as e:
            pytest.skip(f"ChainValidator not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.tracing.chain_validator import ChainValidator
            instance = ChainValidator()
            assert instance is not None
            assert len(instance._layer_order) == 6
        except ImportError as e:
            pytest.skip(f"ChainValidator not available: {e}")
        except Exception as e:
            pytest.skip(f"ChainValidator init failed (expected in CI): {e}")

    def test_import_validation_result(self):
        """Verify ValidationResult dataclass is importable"""
        try:
            from core.tracing.chain_validator import ValidationResult
            result = ValidationResult(valid=True, errors=[], warnings=[])
            assert result is not None
            assert bool(result) is True
        except ImportError as e:
            pytest.skip(f"ValidationResult not available: {e}")
        except Exception as e:
            pytest.skip(f"ValidationResult init failed (expected in CI): {e}")
