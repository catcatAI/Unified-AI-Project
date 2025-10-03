#!/usr/bin/env python3
"""
Unified AI Project 自动化设置脚本
此脚本帮助自动化项目的部分设置过程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        _ = print("错误: 需要Python 3.8或更高版本")
        return False
    return True

def check_pnpm():
    """检查pnpm是否已安装"""
    try:
        subprocess.run(["pnpm", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        _ = print("错误: 未找到pnpm。请先安装pnpm: npm install -g pnpm")
        return False

def setup_backend():
    """设置后端环境"""
    backend_dir = Path("apps/backend")
    if not backend_dir.exists():
        _ = print("错误: 未找到后端目录")
        return False
    
    # 创建虚拟环境
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        _ = print("创建Python虚拟环境...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        except subprocess.CalledProcessError:
            _ = print("错误: 创建虚拟环境失败")
            return False
    
    # 激活虚拟环境并安装依赖
    _ = print("安装Python依赖...")
    pip_path = venv_path / "Scripts" / "pip.exe" if os.name == "nt" else venv_path / "bin" / "pip"
    
    try:
        # 升级pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # 安装主依赖
        requirements_path = backend_dir / "requirements.txt"
        if requirements_path.exists():
            subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)
        
        # 安装开发依赖
        dev_requirements_path = backend_dir / "requirements-dev.txt"
        if dev_requirements_path.exists():
            subprocess.run([str(pip_path), "install", "-r", str(dev_requirements_path)], check=True)
            
        return True
    except subprocess.CalledProcessError:
        _ = print("错误: 安装Python依赖失败")
        return False

def setup_frontend():
    """设置前端环境"""
    _ = print("安装Node.js依赖...")
    try:
        subprocess.run(["pnpm", "install"], check=True)
        return True
    except subprocess.CalledProcessError:
        _ = print("错误: 安装Node.js依赖失败")
        return False

def create_env_files():
    """创建示例环境变量文件"""
    backend_dir = Path("apps/backend")
    env_example_path = backend_dir / ".env.example"
    env_path = backend_dir / ".env"
    
    # 如果.env.example不存在，创建一个
    if not env_example_path.exists():
        env_example_content = """# 数据库配置
DATABASE_URL=sqlite:///./test.db

# API密钥 (请替换为实际的密钥)
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# 服务配置
BACKEND_HOST=localhost
BACKEND_PORT=8000

# 调试配置
DEBUG=true
LOG_LEVEL=INFO

# HSP配置
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
"""
        with open(env_example_path, "w", encoding="utf-8") as f:
            _ = f.write(env_example_content)
        _ = print("已创建 .env.example 文件")
    
    # 如果.env不存在，从.env.example复制
    if not env_path.exists() and env_example_path.exists():
        _ = shutil.copy(env_example_path, env_path)
        _ = print("已创建 .env 文件，请根据需要修改配置")

def main() -> None:
    """主函数"""
    _ = print("Unified AI Project 设置脚本")
    print("=" * 40)
    
    # 检查环境
    if not check_python_version():
        _ = sys.exit(1)
    
    if not check_pnpm():
        _ = sys.exit(1)
    
    # 创建环境变量文件
    _ = print("\n1. 创建环境变量文件...")
    _ = create_env_files()
    
    # 设置后端
    _ = print("\n2. 设置后端环境...")
    if not setup_backend():
        _ = sys.exit(1)
    
    # 设置前端
    _ = print("\n3. 设置前端环境...")
    if not setup_frontend():
        _ = sys.exit(1)
    
    _ = print("\n设置完成!")
    _ = print("\n下一步:")
    _ = print("1. 请检查并修改 apps/backend/.env 文件中的配置")
    _ = print("2. 运行数据库初始化: cd apps/backend && python scripts/init_database.py")
    _ = print("3. 启动开发服务器: pnpm dev")
    _ = print("4. 查看详细配置指南: PROJECT_CONFIGURATION_AND_SETUP_GUIDE.md")

if __name__ == "__main__":
    _ = main()