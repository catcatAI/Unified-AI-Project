import sys
sys.path.insert(0, 'src')
from ai.memory.ham_memory_manager import HAMMemoryManager
import inspect

# 获取query_core_memory方法的签名
method = getattr(HAMMemoryManager, 'query_core_memory')
signature = inspect.signature(method)
print(f"query_core_memory signature: {signature}")

# 获取方法的文档字符串
print(f"query_core_memory docstring: {method.__doc__}")