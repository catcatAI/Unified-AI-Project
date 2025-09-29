#!/usr/bin/env python3
"""
简单的后端启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent / "apps" / "backend"
src_dir = project_root / "src"

# 添加到Python路径
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(src_dir))

_ = print(f"Project root: {project_root}")
_ = print(f"Src dir: {src_dir}")

# 切换到后端目录
_ = os.chdir(project_root)

# 启动Uvicorn服务器
try:
    _ = print("启动后端服务...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "src.services.main_api_server:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ], check=True)
except subprocess.CalledProcessError as e:
    _ = print(f"启动后端服务失败: {e}")
except KeyboardInterrupt:
    _ = print("服务已停止")