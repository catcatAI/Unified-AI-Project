"""
Tests for Integer and Decimal Hash Tables
"""

import pytest
from apps.backend.src.core.state.integer_hash_table import IntegerHashTable
from apps.backend.src.core.state.decimal_hash_table import DecimalHashTable
from decimal import Decimal


class TestIntegerHashTable:
    """測試整數哈希表"""
    
    def test_set_and_get(self):
        """測試基本的 set/get 操作"""
        table = IntegerHashTable()
        
        hash_value = table.set("emotion.level", 5)
        assert isinstance(hash_value, int)
        assert hash_value > 0
        
        value = table.get("emotion.level")
        assert value == 5
    
    def test_get_hash(self):
        """測試獲取哈希值"""
        table = IntegerHashTable()
        
        hash_value = table.set("hormone.active", 1)
        retrieved_hash = table.get_hash("hormone.active")
        
        assert retrieved_hash == hash_value
    
    def test_verify_hash(self):
        """測試哈希驗證"""
        table = IntegerHashTable()
        
        table.set("test.state", 42)
        assert table.verify_hash("test.state") is True
        
        assert table.verify_hash("nonexistent") is False
    
    def test_state_fingerprint(self):
        """測試狀態指紋"""
        table = IntegerHashTable()
        
        initial_fingerprint = table.get_state_fingerprint()
        assert initial_fingerprint == 0
        
        table.set("state1", 1)
        fingerprint1 = table.get_state_fingerprint()
        assert fingerprint1 != 0
        
        table.set("state2", 2)
        fingerprint2 = table.get_state_fingerprint()
        assert fingerprint2 != fingerprint1
    
    def test_verify_causality(self):
        """測試因果鏈驗證"""
        table = IntegerHashTable()
        
        initial = table.get_state_fingerprint()
        table.set("alpha.energy", 80)
        
        change_log = [{"key": "alpha.energy", "value": 80}]
        final = table.get_state_fingerprint()
        
        is_valid = table.verify_causality(initial, final, change_log)
        assert is_valid is True
    
    def test_stats(self):
        """測試統計信息"""
        table = IntegerHashTable()
        
        table.set("state1", 1)
        table.set("state2", 2)
        table.get("state1")
        
        stats = table.get_stats()
        assert stats["entries_count"] == 2
        assert stats["total_sets"] == 2
        assert stats["total_gets"] == 1
    
    def test_clear(self):
        """測試清空哈希表"""
        table = IntegerHashTable()
        
        table.set("state1", 1)
        table.clear()
        
        assert table.get("state1") is None
        assert table.get_state_fingerprint() == 0


class TestDecimalHashTable:
    """測試十進制哈希表"""
    
    def test_set_and_get(self):
        """測試基本的 set/get 操作"""
        table = DecimalHashTable()
        
        hash_value = table.set("hormone.alpha.level", 0.8523)
        assert isinstance(hash_value, int)
        
        value = table.get("hormone.alpha.level")
        assert value == pytest.approx(0.8523, abs=0.0001)
    
    def test_precision_dec4(self):
        """測試 DEC4 精度"""
        table = DecimalHashTable(precision="DEC4")
        
        table.set("test.value", 0.123456789)
        value = table.get_decimal("test.value")
        
        assert value == Decimal('0.1235')
    
    def test_precision_dec8(self):
        """測試 DEC8 精度"""
        table = DecimalHashTable(precision="DEC8")
        
        table.set("test.value", 0.123456789)
        value = table.get_decimal("test.value")
        
        assert value == Decimal('0.12345679')
    
    def test_micro_fluctuation(self):
        """測試微小波動記錄"""
        table = DecimalHashTable()
        
        final_value = table.record_fluctuation(
            key="pain.residual",
            base_value=0.0025,
            fluctuation=0.0003
        )
        
        assert final_value == pytest.approx(0.0028, abs=0.0001)
    
    def test_decay_tracking(self):
        """測試衰減追蹤"""
        table = DecimalHashTable()
        
        decayed = table.track_decay(
            key="hormone.decay",
            initial_value=1.0,
            decay_rate=0.1,
            time_delta=1.0
        )
        
        assert 0.9 < decayed < 0.91
    
    def test_state_fingerprint(self):
        """測試狀態指紋"""
        table = DecimalHashTable()
        
        table.set("state1", 0.5)
        fingerprint1 = table.get_state_fingerprint()
        
        table.set("state2", 0.3)
        fingerprint2 = table.get_state_fingerprint()
        
        assert fingerprint2 != fingerprint1
    
    def test_verify_hash(self):
        """測試哈希驗證"""
        table = DecimalHashTable()
        
        table.set("test.state", 3.14159)
        assert table.verify_hash("test.state") is True
    
    def test_export_state(self):
        """測試狀態導出"""
        table = DecimalHashTable()
        
        table.set("state1", 1.5)
        table.set("state2", 2.3)
        
        export = table.export_state()
        
        assert "entries" in export
        assert "fingerprint" in export
        assert "stats" in export
        assert len(export["entries"]) == 2
