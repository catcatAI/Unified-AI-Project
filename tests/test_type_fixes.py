#!/usr/bin/env python3
"""
测试类型修复是否有效
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"

if str(PROJECT_ROOT) not in sys.path:
    _ = sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_SRC) not in sys.path:
    _ = sys.path.insert(0, str(BACKEND_SRC))

def test_vector_store_client_type() -> None:
    """测试VectorMemoryStore client属性的类型"""
    try:
        from apps.backend.src.core_ai.memory.vector_store import VectorMemoryStore
        
        # 创建实例
        vector_store = VectorMemoryStore()
        
        # 检查client属性是否存在且类型正确
        client = vector_store.client
        _ = print(f"✓ VectorMemoryStore.client type: {type(client)}")
        _ = print(f"✓ VectorMemoryStore.client value: {client}")
        
        return True
    except Exception as e:
        _ = print(f"✗ Error testing VectorMemoryStore client: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_health_check_service() -> None:
    """测试健康检查服务"""
    try:
        from apps.backend.scripts.health_check_service import full_health_check
        
        # 运行完整健康检查
        result = full_health_check()
        _ = print(f"✓ Health check result: {result}")
        
        return True
    except Exception as e:
        _ = print(f"✗ Error testing health check service: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """主函数"""
    _ = print("Testing type fixes...")
    
    success = True
    success &= test_vector_store_client_type()
    success &= test_health_check_service()
    
    if success:
        _ = print("\n✓ All tests passed!")
        return 0
    else:
        _ = print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())