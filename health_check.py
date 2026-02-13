#!/usr/bin/env python3
# Angela AI 健康检查脚本
import os
import sys
import subprocess
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def check_python():
    """检查Python环境"""
    print("🔍 检查Python环境...")
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        print(f"✅ Python版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Python检查失败: {e}")
        return False

def check_dependencies():
    """检查核心依赖"""
    print("\n🔍 检查核心依赖...")
    required_modules = ["fastapi", "uvicorn", "pydantic", "numpy", "pandas"]
    all_ok = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - 未安装")
            all_ok = False
    
    return all_ok

def check_nodejs():
    """检查Node.js环境"""
    print("\n🔍 检查Node.js环境...")
    try:
        result = subprocess.run(["node", "--version"], 
                              capture_output=True, text=True, shell=True)
        print(f"✅ Node.js版本: {result.stdout.strip()}")
        
        result = subprocess.run(["npm", "--version"], 
                              capture_output=True, text=True, shell=True)
        print(f"✅ npm版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Node.js检查失败: {e}")
        return False

def check_node_modules():
    """检查Node.js模块"""
    print("\n🔍 检查Node.js模块...")
    node_modules_path = Path("apps/desktop-app/electron_app/node_modules")
    if node_modules_path.exists():
        module_count = len([d for d in node_modules_path.iterdir() if d.is_dir()])
        print(f"✅ Node.js模块: {module_count}个")
        return True
    else:
        print("❌ Node.js模块不存在")
        return False

def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    config_files = [
        ".env", 
        "requirements.txt", 
        "apps/desktop-app/electron_app/package.json"
    ]
    all_ok = True
    
    for file in config_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - 不存在")
            all_ok = False
    
    return all_ok

def check_scripts():
    """检查关键脚本"""
    print("\n🔍 检查关键脚本...")
    scripts = ["run_angela.py", "quick_start.py"]
    all_ok = True
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"✅ {script}")
        else:
            print(f"❌ {script} - 不存在")
            all_ok = False
    
    return all_ok

def main():
    print("🌟 Angela AI 健康检查")
    print("=" * 50)
    
    checks = [
        check_python,
        check_dependencies,
        check_nodejs,
        check_node_modules,
        check_config_files,
        check_scripts
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 50)
    print("📊 检查结果总结:")
    
    if all(results):
        print("✅ 所有检查通过！系统状态良好。")
        return 0
    else:
        print("⚠️  部分检查未通过，请查看上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())