#!/usr/bin/env python3
"""
Angela AI Quick Start Script
一键快速启动脚本 - 引导用户完成环境检查、配置和启动
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🌟 Angela AI 快速启动向导")
    print("=" * 60)

def check_python():
    """检查 Python 版本"""
    print("\n🔍 检查 Python 环境...")
    if sys.version_info < (3, 10):
        print(f"❌ Python 版本过低: {sys.version_info.major}.{sys.version_info.minor}")
        print("   需要 Python 3.10 或更高版本")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_env_file():
    """检查 .env 文件"""
    print("\n🔍 检查配置文件...")
    env_path = Path(".env")
    if not env_path.exists():
        if Path(".env.example").exists():
            print("⚠️  .env 不存在，正在从 .env.example 创建...")
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ 已创建 .env，请编辑其中的配置（密钥、API Key 等）")
            return False
        else:
            print("❌ 找不到 .env.example")
            return False
    print("✅ .env 存在")
    return True

def check_dependencies():
    """检查核心依赖"""
    print("\n🔍 检查 Python 依赖...")
    required = ["fastapi", "uvicorn", "pydantic", "numpy", "psutil", "cpuinfo"]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    
    if missing:
        print(f"❌ 缺失依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    print("✅ 核心依赖已安装")
    return True

def check_node():
    """检查 Node.js"""
    print("\n🔍 检查 Node.js...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
            return True
    except Exception:
        pass
    print("❌ Node.js 未安装")
    print("请安装 Node.js >= 18 (https://nodejs.org/)")
    return False

def run_health_check():
    """运行健康检查"""
    print("\n🔍 运行健康检查...")
    try:
        result = subprocess.run([sys.executable, "scripts/utils/health_check.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def main():
    print_header()
    
    all_ok = True
    all_ok &= check_python()
    all_ok &= check_env_file()
    all_ok &= check_dependencies()
    all_ok &= check_node()
    
    if not all_ok:
        print("\n⚠️  环境检查未通过，请根据上述提示修复")
        print("\n📚 常用修复命令:")
        print("  pip install -r requirements.txt")
        print("  cp .env.example .env")
        print("  # 编辑 .env 填入密钥和 API Key")
        return 1
    
    # 运行健康检查
    if not run_health_check():
        return 1
    
    print("\n" + "=" * 60)
    print("✅ 环境检查全部通过！")
    print("=" * 60)
    print("\n🚀 启动 Angela AI:")
    print("  python run_angela.py              # 启动全部")
    print("  python run_angela.py --api-only   # 仅启动后端")
    print("  python run_angela.py --health-check  # 健康检查")
    print("\n📚 更多帮助:")
    print("  python run_angela.py --help")
    return 0

if __name__ == "__main__":
    sys.exit(main())
