#!/usr/bin/env python3
"""
完整版系统测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_system_manager_complete import get_complete_system_manager, CompleteSystemConfig

async def test_complete_system():
    """测试完整版系统"""
    print("🚀 开始完整版系统测试...")
    
    try:
        # 测试完整版系统创建
        print("📋 测试1: 完整版系统创建")
        config = CompleteSystemConfig(
            max_workers=32,
            max_concurrent_operations=500,
            enable_motivation_intelligence=True,
            enable_metacognition=True,
            enable_distributed=True,
            enable_performance_monitoring=True
        )
        
        manager = get_complete_system_manager(config)
        print("✅ 完整版系统管理器创建成功")
        
        # 测试完整版系统启动
        print("📋 测试2: 完整版系统启动")
        success = await manager.start_complete_system()
        
        if success:
            print("✅ 完整版系统启动成功")
            
            # 测试系统状态
            print("📋 测试3: 系统状态检查")
            status = manager.get_complete_system_status()
            print(f"✅ 系统状态: {status['system_state']}")
            print(f"✅ 子系统数量: {status['total_systems']}")
            print(f"✅ 活跃系统: {status['active_systems']}")
            print(f"✅ 系统版本: {status['system_version']}")
            
            # 测试动机型智能模块
            if manager.motivation_module:
                print("✅ 动机型智能模块已激活")
            
            # 测试元认知智能模块
            if manager.metacognition_module:
                print("✅ 元认知智能模块已激活")
            
            # 测试企业级功能
            if manager.enterprise_ops:
                print("✅ 企业级功能已激活")
            
            # 测试完整版操作
            print("📋 测试4: 完整版操作执行")
            result = await manager.execute_complete_operation('enterprise.monitor')
            print(f"✅ 企业级监控操作结果: {result['success']}")
            
            # 停止系统
            print("📋 测试5: 系统停止")
            await manager.stop_complete_system()
            print("✅ 完整版系统停止成功")
        else:
            print("❌ 完整版系统启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🏆 完整版系统测试完成！")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_system())
    sys.exit(0 if success else 1)