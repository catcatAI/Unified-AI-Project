"""
测试模块 - test_key_manager

自动生成的测试模块，用于验证系统功能。
"""

import os
import pytest
from apps.backend.src.core.shared.key_manager import UnifiedKeyManager

class TestUnifiedKeyManager:
    """统一密钥管理器测试"""
    
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_not_in_demo_mode(self) -> None:
        """测试非演示模式"""
        # 确保不在演示模式
        if 'DEMO_FLAG' in os.environ:
            del os.environ['DEMO_FLAG']
        
        # 使用模拟配置来禁用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': False,
                'auto_detect': False
            }
        }):
            km = UnifiedKeyManager()
            assert km.demo_mode is False
    
    def test_demo_mode_detection_from_env(self) -> None:
        """测试从环境变量检测演示模式"""
        # 使用模拟配置来启用自动检测
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': False,
                'auto_detect': True,
                'detection_patterns': []
            }
        }):
            # 设置演示模式环境变量
            os.environ['DEMO_FLAG'] = 'true'
            
            km = UnifiedKeyManager()
            assert km.demo_mode is True
            
            # 清理环境变量
            if 'DEMO_FLAG' in os.environ:
                del os.environ['DEMO_FLAG']
    
    def test_get_key_from_environment(self) -> None:
        """测试从环境变量获取密钥"""
        test_key = "test_key_12345"
        os.environ['TEST_API_KEY'] = test_key
        
        # 使用模拟配置来禁用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': False,
                'auto_detect': False
            }
        }):
            km = UnifiedKeyManager()
            result = km.get_key("TEST_API_KEY")
            assert result == test_key
        
        # 清理环境变量
        if 'TEST_API_KEY' in os.environ:
            del os.environ['TEST_API_KEY']
    
    def test_get_key_not_in_environment(self) -> None:
        """测试密钥不在环境变量中"""
        # 确保密钥不在环境变量中
        if 'NONEXISTENT_KEY' in os.environ:
            del os.environ['NONEXISTENT_KEY']
        
        # 使用模拟配置来禁用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': False,
                'auto_detect': False
            }
        }):
            km = UnifiedKeyManager()
            result = km.get_key("NONEXISTENT_KEY")
            assert result is None
    
    def test_get_key_in_demo_mode(self) -> None:
        """测试在演示模式下获取密钥"""
        # 使用模拟配置来启用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': True,
                'fixed_keys': {
                    'ANY_SERVICE_KEY': 'demo_service_key_12345'
                }
            }
        }):
            km = UnifiedKeyManager()
            assert km.demo_mode is True
            
            # 在演示模式下，应该返回模拟的密钥
            result = km.get_key("ANY_SERVICE_KEY")
            assert result is not None
            assert result == 'demo_service_key_12345'
    
    def test_generate_ham_key_not_in_demo_mode(self) -> None:
        """测试在非演示模式下生成HAM密钥"""
        # 使用模拟配置来禁用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': False,
                'auto_detect': False
            }
        }):
            km = UnifiedKeyManager()
            assert km.demo_mode is False
            
            # 在非演示模式下，应该生成真实的HAM密钥
            result = km.generate_ham_key()
            # 根据具体实现，应该返回一个有效的密钥
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_generate_ham_key_in_demo_mode(self) -> None:
        """测试在演示模式下生成HAM密钥"""
        # 使用模拟配置来启用演示模式
        with patch.object(UnifiedKeyManager, '_load_config', return_value={
            'demo_mode': {
                'enabled': True,
                'fixed_keys': {
                    'MIKO_HAM_KEY': 'DEMO_HAM_FIXED_KEY_2025_aGVsbG93b3JsZA=='
                }
            }
        }):
            km = UnifiedKeyManager()
            assert km.demo_mode is True
            
            # 在演示模式下，应该返回模拟的HAM密钥
            result = km.generate_ham_key()
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
            # 在演示模式下，HAM密钥应该是固定的
            assert "DEMO_HAM_FIXED_KEY" in result

if __name__ == "__main__":
    pytest.main([__file__])