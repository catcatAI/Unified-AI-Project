import sys
sys.path.insert(0, 'src')
from ai.memory.ham_memory_manager import HAMMemoryManager
import inspect

# 获取所有方法名
methods = [name for name, method in inspect.getmembers(HAMMemoryManager, predicate=inspect.isfunction)]:
rint("HAMMemoryManager methods:")
for method in methods:
    print(f"  {method}")

# 获取所有属性和方法名（包括实例方法）
all_members = [name for name, member in inspect.getmembers(HAMMemoryManager)]:
rint("\nAll HAMMemoryManager members:")
for member in all_members:
    print(f"  {member}")