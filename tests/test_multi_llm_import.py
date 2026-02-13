"""
测试MultiLLMService导入的脚本
"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMultiLLMImport(unittest.TestCase):
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
    
    def test_multi_llm_import(self):
        """测试MultiLLMService导入"""
        try:
            from core.services.multi_llm_service import MultiLLMService, ModelConfig, ModelProvider
            print("✓ MultiLLMService imported successfully")
            
            # 测试基本功能
            service = MultiLLMService()
            print("✓ MultiLLMService created successfully")
            
            # 验证关键属性存在
            self.assertTrue(hasattr(service, 'providers'))
            self.assertTrue(hasattr(service, 'model_configs'))
            self.assertTrue(hasattr(service, 'usage_stats'))
            print("✓ MultiLLMService has required attributes")
            
        except ImportError as e:
            self.fail(f"Failed to import MultiLLMService: {e}")
        except Exception as e:
            self.fail(f"Failed to create MultiLLMService: {e}")

if __name__ == "__main__":
    unittest.main()