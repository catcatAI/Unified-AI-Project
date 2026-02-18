"""
Integration Tests for Hash+Matrix Dual System with Key Manager
"""

import pytest
from apps.backend.src.core.state.state_hash_manager import StateHashManager
from apps.backend.src.shared.key_manager import UnifiedKeyManager


class TestStateHashManager:
    """測試狀態哈希管理器"""
    
    def test_initialization(self):
        """測試初始化"""
        manager = StateHashManager(precision_mode="DEC4", auto_adapt=False)
        
        assert manager.get_precision_mode() == "DEC4"
    
    def test_set_integer(self):
        """測試設置整數狀態"""
        manager = StateHashManager(auto_adapt=False)
        
        hash_value = manager.set("emotion.level", 5)
        assert isinstance(hash_value, int)
        
        value = manager.get("emotion.level")
        assert value == 5
    
    def test_set_float(self):
        """測試設置浮點數狀態"""
        manager = StateHashManager(auto_adapt=False)
        
        hash_value = manager.set("hormone.alpha", 0.8)
        assert isinstance(hash_value, int)
        
        value = manager.get("hormone.alpha")
        assert value == pytest.approx(0.8, abs=0.0001)
    
    def test_get_hash(self):
        """測試獲取哈希值"""
        manager = StateHashManager(auto_adapt=False)
        
        hash1 = manager.set("state1", 1)
        hash2 = manager.get_hash("state1")
        
        assert hash1 == hash2
    
    def test_global_state_hash(self):
        """測試全局狀態哈希"""
        manager = StateHashManager(auto_adapt=False)
        
        initial = manager.get_state_hash()
        
        manager.set("state1", 1)
        hash1 = manager.get_state_hash()
        assert hash1 != initial
        
        manager.set("state2", 0.5)
        hash2 = manager.get_state_hash()
        assert hash2 != hash1
    
    def test_verify_causality(self):
        """測試因果鏈驗證"""
        manager = StateHashManager(auto_adapt=False)
        
        start = manager.get_state_hash()
        manager.set("alpha.energy", 0.8)
        end = manager.get_state_hash()
        
        is_valid = manager.verify_causality(start, end)
        assert is_valid is True
    
    def test_precision_mode_switching(self):
        """測試精度模式切換"""
        manager = StateHashManager(auto_adapt=False)
        
        manager.set_ram_limit("4GB")
        assert manager.get_precision_mode() == "INT8"
        
        manager.set_ram_limit("16GB")
        assert manager.get_precision_mode() == "DEC4"
    
    def test_export_full_state(self):
        """測試導出完整狀態"""
        manager = StateHashManager(auto_adapt=False)
        
        manager.set("state1", 1)
        manager.set("state2", 0.5)
        
        export = manager.export_full_state()
        
        assert "global_hash" in export
        assert "precision_mode" in export
        assert "integer_table" in export
        assert "decimal_table" in export
        assert "stats" in export
    
    def test_stats(self):
        """測試統計信息"""
        manager = StateHashManager(auto_adapt=False)
        
        manager.set("int_state", 1)
        manager.set("float_state", 0.5)
        
        stats = manager.get_stats()
        
        assert stats["total_operations"] == 2
        assert stats["integer_operations"] == 1
        assert stats["decimal_operations"] == 1


class TestHashKeyIntegration:
    """測試哈希-密鑰集成"""
    
    def test_key_manager_attachment(self):
        """測試密鑰管理器附加"""
        manager = StateHashManager(auto_adapt=False)
        key_manager = UnifiedKeyManager()
        
        manager.set_key_manager(key_manager)
        
        assert manager._key_manager is not None
    
    def test_sign_state_hash(self):
        """測試狀態哈希簽名"""
        manager = StateHashManager(auto_adapt=False)
        key_manager = UnifiedKeyManager()
        manager.set_key_manager(key_manager)
        
        state_hash = manager.get_state_hash()
        signature = manager.sign_state_with_key_a(state_hash)
        
        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_verify_signature(self):
        """測試簽名驗證"""
        manager = StateHashManager(auto_adapt=False)
        key_manager = UnifiedKeyManager()
        manager.set_key_manager(key_manager)
        
        state_hash = manager.get_state_hash()
        signature = manager.sign_state_with_key_a(state_hash)
        
        is_valid = manager.verify_signature(state_hash, signature)
        assert is_valid is True
    
    def test_prevent_forgery(self):
        """測試防偽造"""
        manager = StateHashManager(auto_adapt=False)
        key_manager = UnifiedKeyManager()
        manager.set_key_manager(key_manager)
        
        state_hash = manager.get_state_hash()
        valid_signature = manager.sign_state_with_key_a(state_hash)
        
        is_valid = manager.prevent_state_forgery("test.state", 1, valid_signature)
        assert is_valid is True
        
        fake_signature = "0" * 64
        is_valid = manager.prevent_state_forgery("test.state", 1, fake_signature)
        assert is_valid is False
    
    def test_key_manager_sign_and_verify(self):
        """測試密鑰管理器簽名和驗證"""
        key_manager = UnifiedKeyManager()
        
        state_hash = 12345678901234567890
        signature = key_manager.sign_with_key_a(state_hash)
        
        assert signature is not None
        assert len(signature) == 64
        
        is_valid = key_manager.verify_signature_with_key_a(state_hash, signature)
        assert is_valid is True
    
    def test_state_binding(self):
        """測試狀態綁定"""
        key_manager = UnifiedKeyManager()
        
        state_hash = 98765432109876543210
        binding = key_manager.bind_state_hash(state_hash)
        
        assert "state_hash" in binding
        assert "signature" in binding
        assert "timestamp" in binding
        assert binding["state_hash"] == state_hash
    
    def test_verify_state_binding(self):
        """測試驗證狀態綁定"""
        key_manager = UnifiedKeyManager()
        
        state_hash = 11111111111111111111
        binding = key_manager.bind_state_hash(state_hash)
        
        is_valid = key_manager.verify_state_binding(binding)
        assert is_valid is True
        
        binding["signature"] = "0" * 64
        is_valid = key_manager.verify_state_binding(binding)
        assert is_valid is False
    
    def test_end_to_end_workflow(self):
        """測試端到端工作流"""
        manager = StateHashManager(auto_adapt=False)
        key_manager = UnifiedKeyManager()
        manager.set_key_manager(key_manager)
        
        initial_hash = manager.get_state_hash()
        initial_signature = manager.sign_state_with_key_a(initial_hash)
        
        manager.set("emotion.level", 5)
        manager.set("hormone.alpha", 0.8)
        
        final_hash = manager.get_state_hash()
        final_signature = manager.sign_state_with_key_a(final_hash)
        
        assert initial_hash != final_hash
        assert initial_signature != final_signature
        
        assert manager.verify_signature(initial_hash, initial_signature) is True
        assert manager.verify_signature(final_hash, final_signature) is True
        
        is_causality_valid = manager.verify_causality(initial_hash, final_hash)
        assert is_causality_valid is True
