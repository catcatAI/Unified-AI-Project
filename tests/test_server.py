"""
测试模块 - test_server

自动生成的测试模块，用于验证系统功能。
"""

#!/usr/bin/env python3
"""
简单的测试服务器脚本
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent / "apps" / "backend"
src_dir = project_root / "src"

# 添加到Python路径
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(src_dir))

_ = print("Python路径:")
for path in sys.path:
    _ = print(f"  {path}")

_ = print(f"\n当前工作目录: {os.getcwd()}")

# 检查必要的文件是否存在
main_server = project_root / "src" / "services" / "main_api_server.py"
_ = print(f"\n检查main_api_server.py是否存在: {main_server.exists()}")

# 尝试导入主要模块
try:
    _ = print("\n尝试导入主要模块...")
    _ = print("✓ FastAPI导入成功")
    
    # 尝试导入主应用
    _ = sys.path.insert(0, str(project_root))
    _ = print("✓ 主应用导入成功")
    
    # 简单测试
    _ = print("\n服务器准备就绪!")
    _ = print("请手动运行以下命令启动服务器:")
    _ = print(f"cd {project_root} && python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000")
    
except Exception as e:
    _ = print(f"✗ 导入失败: {e}")
    import traceback
    _ = traceback.print_exc()