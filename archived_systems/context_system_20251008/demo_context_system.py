"""上下文系统演示脚本"""

import logging
from typing import Any
from .manager import ContextManager
from .storage.base import ContextType
from .tool_context import ToolContextManager
from .model_context import ModelContextManager, AgentContextManager
from .dialogue_context import DialogueContextManager
from .memory_context import MemoryContextManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger: Any = logging.getLogger(__name__)

def demo_context_system():
    """演示上下文系统功能"""
    logger.info("=== 上下文系统演示开始 ===")
    
    # 1. 创建上下文管理器
    logger.info("1. 创建上下文管理器...")
    context_manager = ContextManager
    
    # 2. 演示工具上下文
    logger.info("2. 演示工具上下文...")
    demo_tool_context(context_manager)
    
    # 3. 演示模型与代理上下文
    logger.info("3. 演示模型与代理上下文...")
    demo_model_agent_context(context_manager)
    
    # 4. 演示对话上下文
    logger.info("4. 演示对话上下文...")
    demo_dialogue_context(context_manager)
    
    # 5. 演示记忆上下文
    logger.info("5. 演示记忆上下文...")
    demo_memory_context(context_manager)
    
    # 6. 演示上下文检索
    logger.info("6. 演示上下文检索...")
    demo_context_retrieval(context_manager)
    
    logger.info("=== 上下文系统演示结束 ===")

def demo_tool_context(context_manager: ContextManager):
    """演示工具上下文"""
    tool_manager = ToolContextManager(context_manager)
    
    # 创建工具分类
    tool_manager.create_tool_category("cat_001", "代码工具", "代码相关的工具")
    tool_manager.create_tool_category("cat_002", "文件工具", "文件操作相关的工具")
    
    # 注册工具
    tool_manager.register_tool("tool_001", "代码生成器", "生成代码片段", "cat_001")
    tool_manager.register_tool("tool_002", "文件阅读器", "读取文件内容", "cat_002")
    
    # 记录工具使用
    tool_manager.record_tool_usage(
        "tool_001", 
        {"input": "生成一个Python函数"}, 
        "def hello():\n    print('Hello World')", 
        0.5, 
        True
    )
    
    # 获取工具上下文
    tool_context = tool_manager.get_tool_context("tool_001")
    if tool_context:
        logger.info(f"工具上下文: {tool_context}")
    
    logger.info("工具上下文演示完成")

def demo_model_agent_context(context_manager: ContextManager):
    """演示模型与代理上下文"""
    model_manager = ModelContextManager(context_manager)
    agent_manager = AgentContextManager(context_manager)
    
    # 记录模型调用
    model_manager.record_model_call(
        "model_A", 
        "model_B", 
        {"task": "文本摘要"}, 
        "这是摘要内容", 
        1.2, 
        True
    )
    
    # 获取模型上下文
    model_context = model_manager.get_model_context("model_A")
    if model_context:
        logger.info(f"模型上下文: {model_context}")
    
    # 开始代理协作
    collaboration_id = agent_manager.start_collaboration(
        "task_001", 
        ["agent_001", "agent_002"]
    )
    
    # 记录协作步骤
    agent_manager.record_collaboration_step(
        collaboration_id,
        "agent_001",
        "数据收集",
        {"source": "database"},
        {"data": "sample data"},
        0.8
    )
    
    # 完成协作
    agent_manager.complete_collaboration(collaboration_id)
    
    # 获取协作上下文
    collab_context = agent_manager.get_collaboration_context(collaboration_id)
    if collab_context:
        logger.info(f"协作上下文: {collab_context}")
    
    logger.info("模型与代理上下文演示完成")

def demo_dialogue_context(context_manager: ContextManager):
    """演示对话上下文"""
    dialogue_manager = DialogueContextManager(context_manager)
    
    # 开始对话
    conversation_id = "conv_001"
    dialogue_manager.start_conversation(conversation_id, ["user", "ai"])
    
    # 添加消息
    dialogue_manager.add_message(conversation_id, "user", "你好，我想了解AI技术")
    dialogue_manager.add_message(conversation_id, "ai", "您好！AI技术是一个很广泛的领域，包括机器学习、深度学习等")
    dialogue_manager.add_message(conversation_id, "user", "能详细介绍一下机器学习吗？")
    dialogue_manager.add_message(conversation_id, "ai", "机器学习是AI的一个分支，它让计算机能够从数据中学习...")
    
    # 生成上下文摘要
    summary = dialogue_manager.generate_context_summary(conversation_id)
    if summary:
        logger.info(f"对话摘要 - 关键点: {summary.key_points}")
        logger.info(f"对话摘要 - 实体: {summary.entities}")
        logger.info(f"对话摘要 - 情感: {summary.sentiment}")
    
    # 获取对话上下文
    conv_context = dialogue_manager.get_conversation_context(conversation_id)
    if conv_context:
        logger.info(f"对话上下文: {conv_context}")
    
    logger.info("对话上下文演示完成")

def demo_memory_context(context_manager: ContextManager):
    """演示记忆上下文"""
    memory_manager = MemoryContextManager(context_manager)
    
    # 创建记忆
    memory_id_1 = memory_manager.create_memory(
        "用户对AI技术表现出浓厚兴趣", 
        "short_term",
        {"importance": 0.8}
    )
    
    memory_id_2 = memory_manager.create_memory(
        "AI技术包括机器学习、深度学习等分支", 
        "long_term",
        {"category": "technical_knowledge"}
    )
    
    # 访问记忆
    memory_data = memory_manager.access_memory(memory_id_1)
    if memory_data:
        logger.info(f"记忆数据: {memory_data}")
    
    # 更新记忆向量表示
    memory_manager.update_memory_embedding(memory_id_1, [0.1, 0.2, 0.3, 0.4, 0.5])
    
    # 获取记忆上下文
    mem_context = memory_manager.get_memory_context(memory_id_1)
    if mem_context:
        logger.info(f"记忆上下文: {mem_context}")
    
    # 转移记忆
    new_memory_id = memory_manager.transfer_memory(memory_id_1, "long_term")
    if new_memory_id:
        logger.info(f"记忆已转移至: {new_memory_id}")
    
    logger.info("记忆上下文演示完成")

def demo_context_retrieval(context_manager: ContextManager):
    """演示上下文检索"""
    # 创建一些测试上下文
    context_id_1 = context_manager.create_context(
        ContextType.TOOL, 
        {"name": "测试工具", "description": "用于演示检索功能"}
    )
    
    context_id_2 = context_manager.create_context(
        ContextType.MODEL, 
        {"name": "测试模型", "purpose": "演示检索功能"}
    )
    
    # 搜索上下文
    tool_contexts = context_manager.search_contexts("测试", [ContextType.TOOL])
    logger.info(f"找到 {len(tool_contexts)} 个工具上下文")
    
    model_contexts = context_manager.search_contexts("测试", [ContextType.MODEL])
    logger.info(f"找到 {len(model_contexts)} 个模型上下文")
    
    # 获取特定上下文
    context = context_manager.get_context(context_id_1)
    if context:
        logger.info(f"检索到上下文: {context.context_id}, 类型: {context.context_type.value}")
    
    logger.info("上下文检索演示完成")

if __name__ == "__main__":
    demo_context_system