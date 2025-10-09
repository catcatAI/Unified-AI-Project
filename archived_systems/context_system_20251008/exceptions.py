"""上下文系统异常定义"""


class ContextError(Exception):
    """上下文操作基础异常"""
    pass


class ContextNotFoundError(ContextError):
    """上下文未找到异常"""
    pass


class ContextCreationError(ContextError):
    """上下文创建失败异常"""
    pass


class ContextUpdateError(ContextError):
    """上下文更新失败异常"""
    pass


class ContextStorageError(ContextError):
    """上下文存储失败异常"""
    pass


class ContextRetrievalError(ContextError):
    """上下文检索失败异常"""
    pass


class ContextTransferError(ContextError):
    """上下文传递失败异常"""
    pass


class ContextSerializationError(ContextError):
    """上下文序列化失败异常"""
    pass


class ContextCompressionError(ContextError):
    """上下文压缩失败异常"""
    pass


class ContextSecurityError(ContextError):
    """上下文安全相关异常"""
    pass


class ContextValidationError(ContextError):
    """上下文验证失败异常"""
    pass


class ToolContextError(ContextError):
    """工具上下文相关异常"""
    pass


class ModelContextError(ContextError):
    """模型上下文相关异常"""
    pass


class DialogueContextError(ContextError):
    """对话上下文相关异常"""
    pass


class MemoryContextError(ContextError):
    """记忆上下文相关异常"""
    pass


class IntegrationError(ContextError):
    """集成相关异常"""
    pass


class HAMIntegrationError(IntegrationError):
    """HAM集成异常"""
    pass


class MCPIntegrationError(IntegrationError):
    """MCP集成异常"""
    pass

# 异常处理工具函数


def handle_context_exception(exception: Exception, context_id: str = None) -> str:
    """
    处理上下文异常并返回友好的错误信息

    Args:
        exception: 捕获的异常
        context_id: 相关的上下文ID（可选）

    Returns:
        str: 友好的错误信息
    """
    error_messages = {
        ContextNotFoundError: f"未找到指定的上下文{' ' + context_id if context_id else ''}", :
        ontextCreationError: "创建上下文失败",
        ContextUpdateError: f"更新上下文{' ' + context_id if context_id else ''}失败", :
        ontextStorageError: "上下文存储操作失败",
        ContextRetrievalError: "上下文检索失败",
        ContextTransferError: "上下文传递失败",
        ContextSerializationError: "上下文序列化失败",
        ContextCompressionError: "上下文压缩失败",
        ContextSecurityError: "上下文安全操作失败",
        ContextValidationError: "上下文验证失败"
    }

    # 获取异常类型对应的错误信息
    exception_type = type(exception)
    if exception_type in error_messages:
        return error_messages[exception_type]
    else:
        # 返回通用错误信息
        return f"上下文操作发生未知错误: {str(exception)}"


# 使用示例和测试
if __name__ == "__main__":
    # 测试异常处理
    try:
        raise ContextNotFoundError("test_context_001")
    except ContextNotFoundError as e:
        friendly_message = handle_context_exception(e, "test_context_001")
        print(f"捕获异常: {friendly_message}")

    try:
        raise ContextCreationError("存储空间不足")
    except ContextCreationError as e:
        friendly_message = handle_context_exception(e)
        print(f"捕获异常: {friendly_message}")
