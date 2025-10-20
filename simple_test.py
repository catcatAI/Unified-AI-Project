import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, '.')

try:
    # 尝试导入BaseAgent
    from apps.backend.src.agents.base_agent import BaseAgent
    print("BaseAgent导入成功")
except Exception as e:
    print(f"导入失败: {e}")
    print(f"错误类型: {type(e).__name__}")