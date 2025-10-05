"""验证上下文系统基本功能的脚本"""

import sys
import os

# 添加项目根目录到Python路径
project_root: str = os.path.join(os.path.dirname(__file__))
_ = sys.path.append(project_root)

def verify_context_system():
    """验证上下文系统的基本功能"""
    _ = print("开始验证上下文系统...")
    
    try:
        # 导入上下文系统模块
        from apps.backend.src.core_ai.context.manager import ContextManager
        from apps.backend.src.core_ai.context.storage.base import ContextType
        from apps.backend.src.core_ai.context.tool_context import ToolContextManager
        from apps.backend.src.core_ai.context.model_context import ModelContextManager
        from apps.backend.src.core_ai.context.dialogue_context import DialogueContextManager
        from apps.backend.src.core_ai.context.memory_context import MemoryContextManager
        
        _ = print("✓ 成功导入所有上下文系统模块")
        
        # 创建上下文管理器
        context_manager = ContextManager()
        _ = print("✓ 成功创建上下文管理器")
        
        # 测试创建上下文
        context_id = context_manager.create_context(
            ContextType.TOOL, 
            {"name": "测试工具", "version": "1.0"}
        )
        _ = print(f"✓ 成功创建上下文，ID: {context_id}")
        
        # 测试获取上下文
        context = context_manager.get_context(context_id)
        if context and context.context_id == context_id:
            _ = print("✓ 成功获取上下文")
        else:
            _ = print("✗ 获取上下文失败")
            return False
        
        # 测试更新上下文
        success = context_manager.update_context(
            context_id, 
            {"status": "active", "updated_field": "test_value"}
        )
        if success:
            _ = print("✓ 成功更新上下文")
        else:
            _ = print("✗ 更新上下文失败")
            return False
        
        # 测试搜索上下文
        contexts = context_manager.search_contexts("测试", [ContextType.TOOL])
        if len(contexts) > 0:
            _ = print(f"✓ 成功搜索上下文，找到 {len(contexts)} 个结果")
        else:
            _ = print("✗ 搜索上下文未找到结果")
            return False
        
        # 测试工具上下文管理器
        tool_manager = ToolContextManager(context_manager)
        success = tool_manager.create_tool_category("cat_001", "测试分类")
        if success:
            _ = print("✓ 成功创建工具分类")
        else:
            _ = print("✗ 创建工具分类失败")
            return False
        
        # 测试模型上下文管理器
        model_manager = ModelContextManager(context_manager)
        success = model_manager.record_model_call(
            "model_A", "model_B", {"task": "test"}, "result", 1.0, True
        )
        if success:
            _ = print("✓ 成功记录模型调用")
        else:
            _ = print("✗ 记录模型调用失败")
            return False
        
        # 测试对话上下文管理器
        dialogue_manager = DialogueContextManager(context_manager)
        success = dialogue_manager.start_conversation("conv_001", ["user", "ai"])
        if success:
            _ = print("✓ 成功开始对话")
        else:
            _ = print("✗ 开始对话失败")
            return False
        
        # 测试记忆上下文管理器
        memory_manager = MemoryContextManager(context_manager)
        memory_id = memory_manager.create_memory("测试记忆内容", "short_term")
        if memory_id:
            _ = print(f"✓ 成功创建记忆，ID: {memory_id}")
        else:
            _ = print("✗ 创建记忆失败")
            return False
        
        _ = print("\n🎉 所有验证测试通过！上下文系统基本功能正常工作。")
        return True
        
    except Exception as e:
        _ = print(f"✗ 验证过程中发生错误: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_context_system()
    sys.exit(0 if success else 1)