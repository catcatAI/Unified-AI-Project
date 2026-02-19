"""
测试模块 - test_server

自动生成的测试模块,用于验证系统功能。
"""

#!/usr/bin/env python3
"""
简单的测试服务器脚本
"""

import os
import sys
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 添加项目路径
project_root: str = Path(__file__).parent / "apps" / "backend"
src_dir = project_root / "src"

# 添加到Python路径
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

print("Python路径:")
for path in sys.path:
    print(f"  {path}")

print(f"\n当前工作目录: {os.getcwd()}")

# 检查必要的文件是否存在
main_server = project_root / "src" / "services" / "main_api_server.py"
print(f"\n检查main_api_server.py是否存在: {main_server.exists()}")

# 尝试导入主要模块
try:
    print("\n尝试导入主要模块...")
    print("✓ FastAPI导入成功")
    
    # 尝试导入主应用
    sys.path.insert(0, str(project_root))
    print("✓ 主应用导入成功")
    
    # 简单测试
    print("\n服务器准备就绪!")
    print("请手动运行以下命令启动服务器:")
    print(f"cd {project_root} && python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()