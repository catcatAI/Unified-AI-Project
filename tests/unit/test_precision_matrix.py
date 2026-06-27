"""Tests for core.hardware.precision_matrix — matches actual API"""
import pytest


class TestPrecisionMatrix:
    def test_import(self):
        from core.hardware.precision_matrix import (
            ConversionInfo,
            PrecisionConfig,
            PrecisionManager,
            PrecisionMatrix,
        )
        assert PrecisionManager is not None

    def test_instantiation(self):
        from core.hardware.precision_matrix import PrecisionMatrix
        instance = PrecisionMatrix()
        assert hasattr(instance, "entries")
        assert isinstance(instance.entries, dict)

    def test_convert_via_manager(self):
        from core.hardware.precision_matrix import PrecisionConfig, PrecisionLevel, PrecisionManager
        pm = PrecisionManager()
        config = PrecisionConfig(
            source_precision=PrecisionLevel.FP32,
            target_precision=PrecisionLevel.FP16,
        )
        info = pm.convert(config)
        assert info.source == PrecisionLevel.FP32
        assert info.target == PrecisionLevel.FP16

    def test_get_matrix(self):
        from core.hardware.precision_matrix import PrecisionManager
        pm = PrecisionManager()
        matrix = pm.get_matrix()
        assert hasattr(matrix, "entries")

    def test_precision_levels(self):
        from core.hardware.precision_matrix import PrecisionLevel
        assert PrecisionLevel.FP32.value == "fp32"
        assert PrecisionLevel.FP16.value == "fp16"
        assert PrecisionLevel.INT8.value == "int8"

    def test_conversion_info_dataclass(self):
        from core.hardware.precision_matrix import ConversionInfo, PrecisionLevel
        info = ConversionInfo(
            source=PrecisionLevel.FP32,
            target=PrecisionLevel.FP16,
            scale_factor=2.0,
            zero_point=0,
            accuracy_loss=0.01,
        )
        assert info.source == PrecisionLevel.FP32
        assert info.target == PrecisionLevel.FP16
        assert info.scale_factor == 2.0

    def test_convert_precision_function(self):
        from core.hardware.precision_matrix import PrecisionLevel, convert_precision
        result = convert_precision(3.14, PrecisionLevel.FP32, PrecisionLevel.FP16)
        assert result == 3.14

    def test_optimize_for_hardware(self):
        from core.hardware.precision_matrix import PrecisionLevel, optimize_for_hardware
        result = optimize_for_hardware(None, PrecisionLevel.FP16)
        assert result["status"] == "optimized"
        assert result["target_precision"] == "fp16"
