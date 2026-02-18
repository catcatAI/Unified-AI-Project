"""
Tests for Precision Projection Matrix
"""

import pytest
from apps.backend.src.core.state.precision_projection_matrix import (
    PrecisionProjectionMatrix,
    PrecisionMode
)
from decimal import Decimal


class TestPrecisionProjectionMatrix:
    """測試精度投射矩陣"""
    
    def test_initialization(self):
        """測試初始化"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        assert matrix.get_precision_mode() == "DEC4"
    
    def test_force_mode(self):
        """測試強制精度模式"""
        matrix = PrecisionProjectionMatrix(force_mode=PrecisionMode.INT8)
        assert matrix.get_precision_mode() == "INT8"
    
    def test_ram_limit_4gb(self):
        """測試 4GB RAM 限制"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        matrix.set_ram_limit("4GB")
        
        assert matrix.get_precision_mode() == "INT8"
    
    def test_ram_limit_16gb(self):
        """測試 16GB RAM 限制"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        matrix.set_ram_limit("16GB")
        
        assert matrix.get_precision_mode() == "DEC4"
    
    def test_ram_limit_32gb(self):
        """測試 32GB RAM 限制"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        matrix.set_ram_limit("32GB")
        
        assert matrix.get_precision_mode() == "DEC8"
    
    def test_project_to_int8(self):
        """測試投射到 INT8"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        int8_value = matrix.project_to_int8(0.5, min_val=0.0, max_val=1.0)
        
        assert -128 <= int8_value <= 127
        assert isinstance(int8_value, int)
    
    def test_project_from_int8(self):
        """測試從 INT8 恢復"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        original = 0.75
        int8_value = matrix.project_to_int8(original, 0.0, 1.0)
        recovered = matrix.project_from_int8(int8_value, 0.0, 1.0)
        
        assert recovered == pytest.approx(original, abs=0.01)
    
    def test_project_to_dec4(self):
        """測試投射到 DEC4"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        dec4_value = matrix.project_to_dec4(0.123456789)
        
        assert isinstance(dec4_value, Decimal)
        assert dec4_value == Decimal('0.1235')
    
    def test_project_to_dec8(self):
        """測試投射到 DEC8"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        dec8_value = matrix.project_to_dec8(0.123456789)
        
        assert isinstance(dec8_value, Decimal)
        assert dec8_value == Decimal('0.12345679')
    
    def test_convert_auto(self):
        """測試自動轉換"""
        matrix = PrecisionProjectionMatrix(force_mode=PrecisionMode.INT8)
        
        converted = matrix.convert(0.8)
        assert isinstance(converted, int)
        
        matrix = PrecisionProjectionMatrix(force_mode=PrecisionMode.DEC4)
        converted = matrix.convert(0.8)
        assert isinstance(converted, Decimal)
    
    def test_sparse_matrix_creation(self):
        """測試稀疏矩陣創建"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        dense_data = {
            "state1": 0.5,
            "state2": 0.0,
            "state3": 0.8,
            "state4": 0.0,
            "state5": 0.3
        }
        
        sparse = matrix.create_sparse_matrix(dense_data)
        
        assert "non_zero_entries" in sparse
        assert len(sparse["non_zero_entries"]) == 3
        assert "compression_ratio" in sparse
    
    def test_memory_estimate(self):
        """測試內存估算"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        estimates = matrix.get_memory_estimate(1000)
        
        assert "INT8" in estimates
        assert "DEC4" in estimates
        assert "DEC8" in estimates
        assert estimates["INT8"] == 1000
        assert estimates["DEC4"] == 8000
        assert estimates["DEC8"] == 16000
    
    def test_mode_switching(self):
        """測試精度模式切換"""
        matrix = PrecisionProjectionMatrix(auto_detect=False, force_mode=PrecisionMode.INT8)
        
        assert matrix.get_precision_mode() == "INT8"
        
        matrix.force_mode = PrecisionMode.DEC4
        changed = matrix.update_precision_mode()
        
        assert changed is True
        assert matrix.get_precision_mode() == "DEC4"
    
    def test_stats(self):
        """測試統計信息"""
        matrix = PrecisionProjectionMatrix(auto_detect=False)
        
        matrix.convert(0.5)
        matrix.convert(0.8)
        
        stats = matrix.get_stats()
        
        assert stats["total_conversions"] == 2
        assert "current_mode" in stats
        assert "available_ram_mb" in stats
