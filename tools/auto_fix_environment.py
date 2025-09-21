#!/usr/bin/env python3
"""
Unified AI Project 一键式环境修复工具
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
APPS_BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"

def fix_python_path():
    """修复PYTHONPATH环境变量"""
    print("🔧 修复PYTHONPATH环境变量...")
    
    # 获取当前PYTHONPATH
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    
    # 添加项目路径
    paths_to_add = [str(PROJECT_ROOT), str(APPS_BACKEND_DIR), str(APPS_BACKEND_DIR / "src")]
    
    # 检查是否已经包含这些路径
    paths_needed = []
    for path in paths_to_add:
        if path not in current_pythonpath:
            paths_needed.append(path)
    
    if paths_needed:
        new_paths = paths_needed + [current_pythonpath] if current_pythonpath else paths_needed
        new_pythonpath = os.pathsep.join(new_paths)
        
        # 设置环境变量（仅在当前会话中有效）
        os.environ["PYTHONPATH"] = new_pythonpath
        print(f"✅ PYTHONPATH 已更新: {new_pythonpath}")
        
        # 如果需要永久设置，可以写入系统环境变量
        # 这里我们只在当前会话中设置
        return True
    else:
        print("✅ PYTHONPATH 已经包含所需路径")
        return True

def install_missing_python_packages():
    """安装缺失的Python包"""
    print("🔧 检查并安装缺失的Python包...")
    
    required_packages = [
        "fastapi",
        "uvicorn[standard]",
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
            # 尝试导入包
            if package == "uvicorn[standard]":
                __import__("uvicorn")
            else:
                __import__(package.split('[')[0])  # 处理带选项的包名
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 安装缺失的Python包: {', '.join(missing_packages)}")
        try:
            # 切换到后端目录
            original_cwd = os.getcwd()
            os.chdir(APPS_BACKEND_DIR)
            
            # 安装包
            for package in missing_packages:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ 安装 {package} 失败: {result.stderr}")
                    os.chdir(original_cwd)
                    return False
                else:
                    print(f"✅ {package} 安装成功")
            
            os.chdir(original_cwd)
            print("✅ 所有缺失的Python包安装完成")
            return True
        except Exception as e:
            print(f"❌ 安装Python包时出错: {e}")
            return False
    else:
        print("✅ 所有必需的Python包都已安装")
        return True

def install_node_packages():
    """安装Node.js依赖"""
    print("🔧 检查并安装Node.js依赖...")
    
    try:
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # 运行pnpm install
        print("📦 运行 pnpm install...")
        result = subprocess.run([
            "pnpm", "install"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ pnpm install 失败: {result.stderr}")
            os.chdir(original_cwd)
            return False
        else:
            print("✅ Node.js依赖安装成功")
            os.chdir(original_cwd)
            return True
    except Exception as e:
        print(f"❌ 安装Node.js依赖时出错: {e}")
        return False

def setup_backend_environment():
    """设置后端环境"""
    print("🔧 设置后端环境...")
    
    try:
        # 切换到后端目录
        original_cwd = os.getcwd()
        os.chdir(APPS_BACKEND_DIR)
        
        # 创建虚拟环境（如果不存在）
        venv_path = APPS_BACKEND_DIR / "venv"
        if not venv_path.exists():
            print("🐍 创建Python虚拟环境...")
            result = subprocess.run([
                sys.executable, "-m", "venv", "venv"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ 创建虚拟环境失败: {result.stderr}")
                os.chdir(original_cwd)
                return False
            else:
                print("✅ Python虚拟环境创建成功")
        
        # 升级pip
        print("⬆️ 升级pip...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 升级pip失败: {result.stderr}")
            os.chdir(original_cwd)
            return False
        else:
            print("✅ pip升级成功")
        
        os.chdir(original_cwd)
        return True
    except Exception as e:
        print(f"❌ 设置后端环境时出错: {e}")
        return False

def kill_port_processes():
    """终止占用端口的进程"""
    print("🔧 检查并终止占用端口的进程...")
    
    ports = {
        3000: "前端仪表板",
        8000: "后端API",
        3001: "桌面应用"
    }
    
    try:
        import psutil
        
        for port, description in ports.items():
            # 查找占用端口的进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            print(f"⚠️ 发现占用端口 {port} ({description}) 的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                            # 终止进程
                            proc.terminate()
                            proc.wait(timeout=3)
                            print(f"✅ 已终止进程 PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        
        print("✅ 端口检查完成")
        return True
    except ImportError:
        print("⚠️ 未安装psutil包，跳过端口进程检查")
        return True
    except Exception as e:
        print(f"❌ 检查端口进程时出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Unified AI Project 一键式环境修复工具")
    print("=" * 50)
    
    fixes = [
        fix_python_path,
        setup_backend_environment,
        install_missing_python_packages,
        install_node_packages,
        kill_port_processes
    ]
    
    results = []
    for fix in fixes:
        try:
            result = fix()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ 执行修复 {fix.__name__} 时出错: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有修复完成 ({passed}/{total})！环境已修复。")
        return 0
    else:
        print(f"⚠️  {passed}/{total} 项修复完成。请查看上面的警告和错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())