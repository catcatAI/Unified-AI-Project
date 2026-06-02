"""Tests for core.hardware.precision_matrix"""
import pytest
import math


class TestPrecisionMatrix:
    def test_import(self):
        from core.hardware.precision_matrix import (
            PrecisionMatrix, PrecisionManager, ConversionInfo, PrecisionConfig,
        )
        assert PrecisionManager is not None

    def test_instantiation(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        instance = PrecisionMatrix()
        assert len(instance.conversion_table) == 64  # 8x8 precision levels

    def test_get_conversion_fp32_to_fp16(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        info = m.get_conversion("fp32", "fp16")
        assert info is not None
        assert info.source_precision == "fp32"
        assert info.target_precision == "fp16"
        assert 0 < info.loss_rate < 1.0
        assert info.performance_factor == 2.0

    def test_get_conversion_fp16_to_fp32_reversible(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        info = m.get_conversion("fp16", "fp32")
        assert info.loss_rate == 0.0
        assert info.reversible is True

    def test_convert_value_upcast(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        result = m.convert_value(3.14, "fp16", "fp32")
        assert result == 3.14

    def test_convert_value_downcast_lossy(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        converted = m.convert_value(3.14159265, "fp32", "int4")
        assert converted == 1.0  # int4 binary quantize clamps to ±1.0

    def test_estimate_loss_no_loss(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        loss = m.estimate_loss(1.0, 1.0)
        assert loss["absolute"] == 0.0
        assert loss["relative"] == 0.0
        assert loss["db"] == float("inf")

    def test_estimate_loss_with_loss(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        loss = m.estimate_loss(1.0, 0.9)
        assert loss["absolute"] == pytest.approx(0.1)
        assert loss["relative"] == pytest.approx(0.1)
        assert loss["db"] > 0

    def test_get_path_same_source_target(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        path = m.get_path("fp32", "fp32")
        assert path == [("fp32", "fp32")]

    def test_validate_precision_supported(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        m = PrecisionMatrix()
        result = m.validate_precision("fp32")
        assert result["supported"] is True

    def test_precision_manager_defaults(self):
        from core.hardware.precision_matrix import PrecisionManager
        pm = PrecisionManager()
        assert pm.config.working_precision == "fp32"
        assert pm.config.computation_precision == "fp16"
        assert pm.config.network_precision == "int8"
