#!/usr/bin/env python3
"""
简化测试统一系统管理器
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_system_manager import UnifiedSystemManager, SystemConfig, get_unified_system_manager, start_unified_system, stop_unified_system, get_system_status

async def test_unified_system_simple():
    """简化测试统一系统管理器"""
    print("🚀 开始简化测试统一系统管理器...")
    
    try,
        # 创建系统管理器实例
        config == SystemConfig()
        manager == UnifiedSystemManager(config)
        
        print("✅ 统一系统管理器创建成功")
        
        # 获取系统状态
        status = manager.get_system_summary()
        print(f"系统摘要,")
        print(f"  - 总系统数, {status['total_systems']}")
        print(f"  - 活跃系统数, {status['active_systems']}")
        print(f"  - 错误系统数, {status['error_systems']}")
        
        # 测试传输块创建
        from unified_system_manager import create_transfer_block
        test_block = create_transfer_block(
            source_system="test_system",
            target_system="memory_manager",
            content_type="test_data",
            content == {"test_key": "test_value", "timestamp": "2025-10-08T21,00,00"},
    priority=2
        )
        print(f"✅ 传输块创建成功, {test_block.block_id}")
        
        # 测试系统操作
        print("\n📋 测试系统操作,")
        
        # 测试修复系统状态
        repair_status = manager.get_system_status('auto_repair')
        if repair_status,::
            print(f"  - 自动修复系统, {repair_status['status']}")
        else,
            print("  - 自动修复系统, 未找到")
        
        # 测试内存管理器状态
        memory_status = manager.get_system_status('memory_manager')
        if memory_status,::
            print(f"  - 记忆管理器, {memory_status['status']}")
        else,
            print("  - 记忆管理器, 未找到")
        
        # 测试上下文管理器状态
        context_status = manager.get_system_status('context_manager')
        if context_status,::
            print(f"  - 上下文管理器, {context_status['status']}")
        else,
            print("  - 上下文管理器, 未找到")
        
        print("\n✅ 简化测试完成")
        
        # 打印详细的系统状态
        print("\n📊 详细系统状态,")
        all_status = manager.get_system_status()
        for system_name, info in all_status.items():::
            print(f"  {system_name} {info['status']} (健康分数, {info['metrics']['system_health_score'].2f})")
        
        return True
        
    except Exception as e,::
        print(f"❌ 测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    # 运行简化测试
    success = asyncio.run(test_unified_system_simple())
    if success,::
        print("\n🎉 所有测试通过！")
    else,
        print("\n💥 测试失败！")
        sys.exit(1)