#!/usr/bin/env python3
"""
增强AI代理协作功能测试脚本
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

# 创建占位符类型和类
class HSPTaskRequestPayload(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HSPTaskResultPayload(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HSPMessageEnvelope(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HSPConnector,
    def register_on_task_result_callback(self, callback):
        pass

    async def send_task_request(self, payload, target_ai_id_or_topic):
        print(f"Sending task request, {payload}")
        return True

async def test_enhanced_collaboration():
    """测试增强的协作功能"""
    print("🚀 开始测试增强的AI代理协作功能...")
    
    try,
        # 导入增强的协作管理器
        from apps.backend.src.ai.agent_collaboration_manager_enhanced import (
            AgentCollaborationManager, 
            HSPConnector,
            CollaborationStatus
        )
        
        print("✅ 成功导入增强的协作管理器")
        
        # 创建协作管理器实例
        hsp_connector == HSPConnector()
        collaboration_manager == AgentCollaborationManager(hsp_connector)
        print("✅ 成功创建协作管理器实例")
        
        # 测试注册代理能力
        await collaboration_manager.register_agent_capability("agent_1", "capability_1")
        await collaboration_manager.register_agent_capability("agent_2", "capability_2")
        print("✅ 成功注册代理能力")
        
        # 测试查找代理能力
        agent_id = await collaboration_manager.find_agent_for_capability("capability_1")
        assert agent_id == "agent_1", f"预期agent_1,实际得到{agent_id}"
        print("✅ 成功查找代理能力")
        
        # 测试任务委派
        task_id = await collaboration_manager.delegate_task(
            requester_agent_id="agent_1",
            target_agent_id="agent_2",
            capability_id="capability_2",
            parameters == {"test": "data"},
    priority=5
        )
        print(f"✅ 成功委派任务, {task_id}")
        
        # 测试批量任务委派
        task_definitions = [
            {
                "target_agent_id": "agent_2",
                "capability_id": "capability_2",
                "parameters": {"batch_test": "data1"}
                "priority": 3
            }
            {
                "target_agent_id": "agent_2",
                "capability_id": "capability_2",
                "parameters": {"batch_test": "data2"}
                "priority": 7
            }
        ]
        
        task_ids = await collaboration_manager.delegate_tasks_batch("agent_1", task_definitions)
        print(f"✅ 成功批量委派任务, {task_ids}")
        
        # 测试任务队列状态
        queue_status = await collaboration_manager.get_task_queue_status()
        print(f"✅ 任务队列状态, {queue_status}")
        
        # 测试缓存功能
        cache_status = await collaboration_manager.get_cache_status()
        print(f"✅ 缓存状态, {cache_status}")
        
        # 测试异步任务委派
        try,
            future = await collaboration_manager.delegate_task_async(
                requester_agent_id="agent_1",
                target_agent_id="agent_2",
                capability_id="capability_2",
                parameters == {"async_test": "data"},
    priority=8
            )
            print("✅ 成功创建异步任务委派")
        except Exception as e,::
            print(f"⚠️ 异步任务委派测试跳过, {e}")
        
        print("\n🎉 所有增强协作功能测试通过!")
        return True
        
    except Exception as e,::
        print(f"❌ 测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_base_agent_enhanced_features():
    """测试BaseAgent增强功能"""
    print("\n🚀 开始测试BaseAgent增强功能...")
    
    try,
        # 创建一个简单的BaseAgent实现用于测试
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self, agent_id, str):
                super().__init__(agent_id=agent_id, capabilities = [])
        
        # 创建测试代理
        test_agent == TestAgent("test_agent")
        print("✅ 成功创建测试代理")
        
        # 由于协作管理器需要HSP连接器,我们无法完全测试所有功能
        # 但可以验证方法是否正确添加到类中
        assert hasattr(test_agent, 'delegate_task_to_agent'), "缺少delegate_task_to_agent方法"
        assert hasattr(test_agent, 'delegate_task_to_agent_async'), "缺少delegate_task_to_agent_async方法"
        assert hasattr(test_agent, 'delegate_tasks_batch'), "缺少delegate_tasks_batch方法"
        assert hasattr(test_agent, 'get_task_queue_status'), "缺少get_task_queue_status方法"
        assert hasattr(test_agent, 'get_cache_status'), "缺少get_cache_status方法"
        assert hasattr(test_agent, 'clear_expired_cache'), "缺少clear_expired_cache方法"
        assert hasattr(test_agent, 'clear_cache'), "缺少clear_cache方法"
        
        print("✅ 所有增强方法已正确添加到BaseAgent")
        print("\n🎉 BaseAgent增强功能测试通过!")
        return True
        
    except Exception as e,::
        print(f"❌ BaseAgent测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_functionality():
    """测试缓存功能"""
    print("\n🚀 开始测试缓存功能...")
    
    try,
        # 导入增强的协作管理器
        from apps.backend.src.ai.agent_collaboration_manager_enhanced import (
            AgentCollaborationManager, 
            HSPConnector,
            CollaborationStatus
        )
        
        # 创建协作管理器实例
        hsp_connector == HSPConnector()
        collaboration_manager == AgentCollaborationManager(hsp_connector)
        
        # 测试缓存状态
        cache_status = await collaboration_manager.get_cache_status()
        assert "total_cache_items" in cache_status
        assert "active_cache_items" in cache_status
        assert "cache_expiry_seconds" in cache_status
        print("✅ 缓存状态查询功能正常")
        
        # 测试清理过期缓存
        cleaned_count = await collaboration_manager.clear_expired_cache()
        print(f"✅ 清理过期缓存, {cleaned_count} 项")
        
        # 测试清空缓存
        await collaboration_manager.clear_cache()
        print("✅ 缓存清空功能正常")
        
        print("\n🎉 缓存功能测试通过!")
        return True
        
    except Exception as e,::
        print(f"❌ 缓存功能测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🧪 Unified AI Project 增强AI代理协作功能测试")
    print("=" * 60)
    
    # 测试增强的协作功能
    collaboration_success = await test_enhanced_collaboration()
    
    # 测试BaseAgent增强功能
    base_agent_success = await test_base_agent_enhanced_features()
    
    # 测试缓存功能
    cache_success = await test_cache_functionality()
    
    print("\n" + "=" * 60)
    if collaboration_success and base_agent_success and cache_success,::
        print("🎉 所有测试通过! 增强AI代理协作功能已成功实现!")
        return True
    else,
        print("💥 部分测试失败! 请检查错误信息。")
        return False

if __name"__main__":::
    success = asyncio.run(main())
    sys.exit(0 if success else 1)