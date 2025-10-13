#!/usr/bin/env python3
"""
简单的后端测试
"""

import sys
import os
from pathlib import Path

# 添加后端路径
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

print("Python路径:")
for p in sys.path[:3]:
    print(f"  {p}")

print("\n测试基础导入...")

# 测试基础模块
try:
    import fastapi
    print("✓ FastAPI可用")
except Exception as e:
    print(f"✗ FastAPI不可用: {e}")

try:
    import uvicorn
    print("✓ Uvicorn可用")
except Exception as e:
    print(f"✗ Uvicorn不可用: {e}")

try:
    import psutil
    print("✓ Psutil可用")
except Exception as e:
    print(f"✗ Psutil不可用: {e}")

print("\n测试项目模块...")

# 测试main.py
try:
    from main import create_app
    print("✓ main.py导入成功")
    app = create_app()
    print("✓ FastAPI应用创建成功")
except Exception as e:
    print(f"✗ main.py导入失败: {e}")
    import traceback
    traceback.print_exc()