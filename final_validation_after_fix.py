import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
backend_src = project_root / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

def validate_imports():
    """验证关键模块的导入"""
    print("=== Unified-AI-Project 重构后导入验证 ===")
    
    # 测试核心服务导入
    try:
        import apps.backend.src.core_services
        print("✓ core_services 模块导入成功")
    except Exception as e:
        print(f"✗ core_services 模块导入失败: {e}")
        return False
    
    # 测试AI模块导入
    try:
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        print("✓ BaseAgent 导入成功")
    except Exception as e:
        print(f"✗ BaseAgent 导入失败: {e}")
        return False
        
    try:
        from apps.backend.src.ai.dialogue.dialogue_manager import DialogueManager
        print("✓ DialogueManager 导入成功")
    except Exception as e:
        print(f"✗ DialogueManager 导入失败: {e}")
        return False
        
    try:
        from apps.backend.src.ai.learning.learning_manager import LearningManager
        print("✓ LearningManager 导入成功")
    except Exception as e:
        print(f"✗ LearningManager 导入失败: {e}")
        return False
        
    # 测试核心模块导入
    try:
        from apps.backend.src.core.services.multi_llm_service import MultiLLMService
        print("✓ MultiLLMService 导入成功")
    except Exception as e:
        print(f"✗ MultiLLMService 导入失败: {e}")
        return False
        
    try:
        from apps.backend.src.core.hsp.connector import HSPConnector
        print("✓ HSPConnector 导入成功")
    except Exception as e:
        print(f"✗ HSPConnector 导入失败: {e}")
        return False
        
    try:
        from apps.backend.src.core.tools.tool_dispatcher import ToolDispatcher
        print("✓ ToolDispatcher 导入成功")
    except Exception as e:
        print(f"✗ ToolDispatcher 导入失败: {e}")
        return False
    
    # 测试MCP连接器导入
    try:
        from apps.backend.src.mcp.connector import MCPConnector
        print("✓ MCPConnector 导入成功")
    except Exception as e:
        print(f"✗ MCPConnector 导入失败: {e}")
        return False
        
    print("\n=== 所有关键模块导入验证通过 ===")
    return True

def validate_directory_structure():
    """验证目录结构"""
    print("\n=== 目录结构验证 ===")
    
    required_dirs = [
        "apps/backend/src/ai",
        "apps/backend/src/ai/agents",
        "apps/backend/src/ai/agents/base",
        "apps/backend/src/ai/dialogue",
        "apps/backend/src/ai/learning",
        "apps/backend/src/ai/memory",
        "apps/backend/src/ai/personality",
        "apps/backend/src/ai/emotion",
        "apps/backend/src/ai/trust",
        "apps/backend/src/ai/discovery",
        "apps/backend/src/ai/crisis",
        "apps/backend/src/ai/time",
        "apps/backend/src/ai/formula_engine",
        "apps/backend/src/core",
        "apps/backend/src/core/services",
        "apps/backend/src/core/managers",
        "apps/backend/src/core/tools",
        "apps/backend/src/core/hsp",
        "apps/backend/src/mcp"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"✗ 目录不存在: {dir_path}")
            return False
        print(f"✓ 目录存在: {dir_path}")
    
    print("\n=== 目录结构验证通过 ===")
    return True

def main():
    print("开始验证重构后的项目...")
    
    # 验证目录结构
    if not validate_directory_structure():
        print("\n❌ 目录结构验证失败")
        sys.exit(1)
    
    # 验证导入
    if not validate_imports():
        print("\n❌ 导入验证失败")
        sys.exit(1)
    
    print("\n🎉 所有验证通过！项目重构完成。")

if __name__ == "__main__":
    main()