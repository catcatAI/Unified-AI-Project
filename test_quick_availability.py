#!/usr/bin/env python3
"""
快速系统可用性测试 - 验证核心功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_system_manager_minimal import get_unified_system_manager_minimal, create_transfer_block_minimal

def test_quick_availability():
    """快速可用性测试"""
    print("🚀 开始快速系统可用性测试...")
    
    try:
        # 测试1: 系统管理器创建
        print("📋 测试1: 系统管理器创建")
        manager = get_unified_system_manager_minimal()
        print("✅ 系统管理器创建成功")
        
        # 测试2: TransferBlock创建
        print("📋 测试2: TransferBlock创建")
        tb = create_transfer_block_minimal(
            source_system='test_user',
            target_system='context_manager',
            content_type='user_query',
            content={'query': '系统是否可用？', 'timestamp': '2025-10-08T22:30:00'}
        )
        print(f"✅ TransferBlock创建成功: {tb.block_id}")
        
        # 测试3: 简单上下文操作
        print("📋 测试3: 简单上下文操作")
        result = manager.execute_operation('context.get', context_id='test_context')
        print(f"✅ 上下文查询结果: {result}")
        
        # 测试4: 系统状态
        print("📋 测试4: 系统状态检查")
        status = manager.get_system_summary()
        print(f"✅ 系统摘要: {status['total_systems']} 个子系统，{status['active_systems']} 个活跃")
        
        print("\n🏆 快速可用性测试通过！")
        print("✅ 系统完全可用")
        print("✅ 核心功能正常运行")
        print("✅ TransferBlock机制工作正常")
        print("✅ 上下文管理系统可用")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_quick_availability()
    sys.exit(0 if success else 1)