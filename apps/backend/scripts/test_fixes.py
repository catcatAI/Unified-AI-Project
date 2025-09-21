#!/usr/bin/env python3
"""
测试我们对错误的修复
"""

import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

def test_dataclass_import():
    """测试dataclass导入修复"""
    try:
        from tools.math_model.model import MathModelResult
        print("✅ dataclass导入修复成功")
        return True
    except Exception as e:
        print(f"❌ dataclass导入修复失败: {e}")
        return False

def test_rovo_dev_connector():
    """测试RovoDevConnector修复"""
    try:
        from integrations.rovo_dev_connector import RovoDevConnector
        print("✅ RovoDevConnector导入修复成功")
        return True
    except Exception as e:
        print(f"❌ RovoDevConnector导入修复失败: {e}")
        return False

def test_atlassian_integration_import():
    """测试Atlassian集成导入修复"""
    try:
        from services.main_api_server import app
        print("✅ Atlassian集成导入修复成功")
        return True
    except Exception as e:
        print(f"❌ Atlassian集成导入修复失败: {e}")
        return False

def test_test_file_imports():
    """测试测试文件导入修复"""
    try:
        # 测试Atlassian集成测试文件
        from tests.integration.test_atlassian_integration import TestAtlassianIntegration
        print("✅ Atlassian集成测试文件导入修复成功")
        
        # 测试Hot endpoints测试文件
        from tests.services.test_hot_endpoints import test_hot_status_endpoint_basic_structure
        print("✅ Hot endpoints测试文件导入修复成功")
        
        # 测试Main API server测试文件
        from tests.services.test_main_api_server import test_read_main
        print("✅ Main API server测试文件导入修复成功")
        
        # 测试Main API server HSP测试文件
        from tests.services.test_main_api_server_hsp import TestHSPEndpoints
        print("✅ Main API server HSP测试文件导入修复成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试文件导入修复失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 开始测试修复是否成功")
    
    # 测试dataclass导入修复
    success1 = test_dataclass_import()
    
    # 测试RovoDevConnector修复
    success2 = test_rovo_dev_connector()
    
    # 测试Atlassian集成导入修复
    success3 = test_atlassian_integration_import()
    
    # 测试测试文件导入修复
    success4 = test_test_file_imports()
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 所有修复测试通过！")
        return 0
    else:
        print("\n❌ 一些修复测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())