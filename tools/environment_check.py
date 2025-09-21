#!/usr/bin/env python3
"""
Unified AI Project 环境自检工具
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
APPS_BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本 {version.major}.{version.minor}.{version.micro} 满足要求")
        return True
    else:
        print(f"❌ Python版本 {version.major}.{version.minor}.{version.micro} 不满足要求（需要>=3.8）")
        return False

def check_node_version():
    """检查Node.js版本"""
    print("🔍 检查Node.js版本...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js版本 {version} 已安装")
            return True
        else:
            print("❌ Node.js未安装或不可用")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def check_pnpm():
    """检查pnpm"""
    print("🔍 检查pnpm...")
    try:
        # 直接运行pnpm --version
        result = subprocess.run(["cmd", "/c", "pnpm", "--version"], capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ pnpm版本 {version} 已安装")
            return True
        else:
            print("❌ pnpm未安装或不可用")
            return False
    except Exception as e:
        print(f"❌ 检查pnpm时出错: {e}")
        return False

def check_python_packages():
    """检查Python包依赖"""
    print("🔍 检查Python包依赖...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "numpy",
        "pandas",
        "requests",
        "pytest",
        "chromadb"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    if missing_packages:
        print(f"⚠️ 缺少以下Python包: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ 所有必需的Python包都已安装")
        return True

def check_node_packages():
    """检查Node.js包依赖"""
    print("🔍 检查Node.js包依赖...")
    package_json_path = PROJECT_ROOT / "package.json"
    if not package_json_path.exists():
        print("❌ package.json 文件不存在")
        return False
    
    try:
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_json = json.load(f)
        
        dependencies = package_json.get("dependencies", {})
        dev_dependencies = package_json.get("devDependencies", {})
        
        print(f"✅ package.json 文件存在，包含 {len(dependencies)} 个依赖和 {len(dev_dependencies)} 个开发依赖")
        return True
    except Exception as e:
        print(f"❌ 读取 package.json 文件时出错: {e}")
        return False

def check_project_structure():
    """检查项目结构"""
    print("🔍 检查项目结构...")
    required_paths = [
        PROJECT_ROOT / "apps" / "backend",
        PROJECT_ROOT / "apps" / "frontend-dashboard",
        PROJECT_ROOT / "apps" / "backend" / "src",
        PROJECT_ROOT / "apps" / "backend" / "src" / "services" / "main_api_server.py",
        PROJECT_ROOT / "apps" / "backend" / "scripts" / "smart_dev_runner.py",
        PROJECT_ROOT / "apps" / "frontend-dashboard" / "server.ts"
    ]
    
    missing_paths = []
    for path in required_paths:
        if not path.exists():
            missing_paths.append(str(path))
            print(f"❌ 路径不存在: {path}")
        else:
            print(f"✅ 路径存在: {path}")
    
    if missing_paths:
        print(f"⚠️ 缺少以下路径: {', '.join(missing_paths)}")
        return False
    else:
        print("✅ 项目结构完整")
        return True

def check_environment_variables():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    recommended_vars = [
        "PYTHONPATH",
        "NODE_ENV"
    ]
    
    missing_vars = []
    for var in recommended_vars:
        if var not in os.environ:
            missing_vars.append(var)
            print(f"⚠️ 环境变量未设置: {var}")
        else:
            print(f"✅ 环境变量已设置: {var}")
    
    # 检查PYTHONPATH是否包含项目路径
    pythonpath = os.environ.get("PYTHONPATH", "")
    if str(PROJECT_ROOT) in pythonpath or str(APPS_BACKEND_DIR) in pythonpath:
        print("✅ PYTHONPATH 包含项目路径")
    else:
        print("⚠️ PYTHONPATH 未包含项目路径")
    
    return True

def check_ports():
    """检查端口可用性"""
    print("🔍 检查端口可用性...")
    ports = {
        3000: "前端仪表板",
        8000: "后端API",
        3001: "桌面应用"
    }
    
    try:
        import socket
        for port, description in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"⚠️ 端口 {port} ({description}) 已被占用")
            else:
                print(f"✅ 端口 {port} ({description}) 可用")
        return True
    except Exception as e:
        print(f"❌ 检查端口时出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Unified AI Project 环境自检工具")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_node_version,
        check_pnpm,
        check_python_packages,
        check_node_packages,
        check_project_structure,
        check_environment_variables,
        check_ports
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ 执行检查 {check.__name__} 时出错: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有检查通过 ({passed}/{total})！环境配置正确。")
        return 0
    else:
        print(f"⚠️  {passed}/{total} 项检查通过。请查看上面的警告和错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())