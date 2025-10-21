import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_imports():
    """测试导入功能"""
    print("🚀 开始测试导入功能...")
    
    try,
        # 测试导入HSP类型
        from apps.backend.src.core.hsp.types import (
            HSPTaskRequestPayload,
            HSPTaskResultPayload,
            HSPMessageEnvelope
        )
        print("✅ 成功导入HSP类型")
        
        # 测试导入BaseAgent
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        print("✅ 成功导入BaseAgent")
        
        # 测试导入增强的协作管理器
        # 使用相对导入路径
        sys.path.append(str(Path(__file__).parent / "apps" / "backend" / "src"))
        from ai.agent_collaboration_manager_enhanced import (
            AgentCollaborationManager,
            HSPConnector,
            CollaborationStatus
        )
        print("✅ 成功导入增强的协作管理器")
        
        return True
    except Exception as e,::
        print(f"❌ 导入测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🧪 Unified AI Project 导入测试")
    print("=" * 40)
    
    success = await test_imports()
    
    print("\n" + "=" * 40)
    if success,::
        print("🎉 导入测试通过!")
        return True
    else,
        print("💥 导入测试失败!")
        return False

if __name"__main__":::
    success = asyncio.run(main())
    sys.exit(0 if success else 1)