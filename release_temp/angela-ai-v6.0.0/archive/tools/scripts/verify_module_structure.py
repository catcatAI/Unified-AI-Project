import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

def verify_module_structure():
    """验证模块结构是否正确"""
    print("开始验证模块结构...")
    
    # 测试导入核心模块
    try,
        # 测试导入对话管理器
        from apps.backend.src.core_ai.dialogue.dialogue_manager import DialogueManager
        print("✓ 成功导入 DialogueManager")
        
        # 测试导入内存管理器
        from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
        print("✓ 成功导入 HAMMemoryManager")
        
        # 测试导入学习管理器
        from apps.backend.src.core_ai.learning.learning_manager import LearningManager
        print("✓ 成功导入 LearningManager")
        
        # 测试导入个性管理器
        from apps.backend.src.core_ai.personality.personality_manager import PersonalityManager
        print("✓ 成功导入 PersonalityManager")
        
        # 测试导入智能体模块
        from apps.backend.src.core_ai.agents.base.base_agent import BaseAgent
        print("✓ 成功导入 BaseAgent")
        
        # 测试导入上下文管理器
        from apps.backend.src.core_ai.context.manager import ContextManager
        print("✓ 成功导入 ContextManager")
        
        print("\n🎉 所有模块导入测试通过！模块结构正确。")
        return True
        
    except ImportError as e,::
        print(f"❌ 模块导入失败, {e}")
        return False
    except Exception as e,::
        print(f"❌ 验证过程中出现错误, {e}")
        return False

if __name"__main__":::
    success = verify_module_structure()
    sys.exit(0 if success else 1)