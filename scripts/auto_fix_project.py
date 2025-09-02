#!/usr/bin/env python3
"""
一键修复脚本
"""

import os
import subprocess
import sys
from pathlib import Path

def check_virtual_environment():
    """检查虚拟环境"""
    if not Path("venv").exists():
        print("创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])

def activate_virtual_environment():
    """激活虚拟环境"""
    if os.name == "nt":  # Windows
        activate_script = Path("venv") / "Scripts" / "activate.bat"
    else:  # Unix/Linux/macOS
        activate_script = Path("venv") / "bin" / "activate"
    
    # We'll use the virtual environment's Python directly
    if os.name == "nt":  # Windows
        python_executable = Path("venv") / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        python_executable = Path("venv") / "bin" / "python"
    
    return str(python_executable)

def update_pip(python_executable):
    """更新pip"""
    print("更新pip...")
    subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_dependencies(python_executable):
    """安装依赖"""
    print("安装依赖...")
    # Check if we're in the backend directory
    if Path.cwd().name == "backend":
        requirements_files = ["requirements.txt", "requirements-dev.txt"]
    else:
        # Assume we're in the project root
        requirements_files = [
            "apps/backend/requirements.txt",
            "apps/backend/requirements-dev.txt"
        ]
    
    for req_file in requirements_files:
        if Path(req_file).exists():
            print(f"Installing from {req_file}...")
            subprocess.run([python_executable, "-m", "pip", "install", "-r", req_file])

def check_dependency_conflicts(python_executable):
    """检查依赖冲突"""
    print("检查依赖冲突...")
    subprocess.run([python_executable, "-m", "pip", "check"])

def check_env_vars(python_executable):
    """检查环境变量"""
    print("检查环境变量...")
    script_path = Path(__file__).parent / "check_env_vars.py"
    subprocess.run([python_executable, str(script_path)])

def main():
    """主函数"""
    print("开始修复项目常见问题...")
    
    # 检查并创建虚拟环境
    check_virtual_environment()
    
    # 激活虚拟环境
    python_executable = activate_virtual_environment()
    
    # 更新pip
    update_pip(python_executable)
    
    # 安装依赖
    install_dependencies(python_executable)
    
    # 检查依赖冲突
    check_dependency_conflicts(python_executable)
    
    # 检查环境变量
    check_env_vars(python_executable)
    
    print("修复完成!")

if __name__ == "__main__":
    main()