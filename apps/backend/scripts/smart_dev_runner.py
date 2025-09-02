#!/usr/bin/env python3
"""
智能开发服务器运行器 - 在启动开发服务器时自动检测和修复错误
"""

import os
import sys
import subprocess
import re
import time
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

def setup_environment():
    """设置环境"""
    # 添加项目路径
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
        
    # 激活虚拟环境
    venv_path = PROJECT_ROOT / "venv"
    if venv_path.exists():
        if sys.platform == "win32":
            activate_script = venv_path / "Scripts" / "activate.bat"
        else:
            activate_script = venv_path / "bin" / "activate"
        
        # 设置环境变量
        if sys.platform == "win32":
            os.environ["PATH"] = f"{venv_path / 'Scripts'}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ["PATH"] = f"{venv_path / 'bin'}{os.pathsep}{os.environ['PATH']}"

def detect_dev_errors(stderr_output, stdout_output):
    """检测开发服务器启动错误"""
    errors = []
    
    # 合并输出
    full_output = (stdout_output or "") + (stderr_output or "")
    
    # 检测导入错误
    import_error_patterns = [
        r"ModuleNotFoundError: No module named '([^']+)'",
        r"ImportError: cannot import name '([^']+)'",
        r"ImportError: No module named '([^']+)'",
        r"NameError: name '([^']+)' is not defined",
    ]
    
    for pattern in import_error_patterns:
        matches = re.findall(pattern, full_output)
        for match in matches:
            if match not in errors:
                errors.append(match)
    
    # 检测路径错误
    path_error_patterns = [
        r"No module named 'core_ai",
        r"No module named 'hsp",
        r"from \.\.core_ai",
    ]
    
    for pattern in path_error_patterns:
        if re.search(pattern, full_output):
            errors.append("path_error")
            
    # 检测Uvicorn错误
    if "uvicorn" in full_output.lower() and "error" in full_output.lower():
        errors.append("uvicorn_error")
        
    return errors

def run_auto_fix():
    """运行自动修复工具"""
    print("🔍 检测到导入错误，正在自动修复...")
    
    try:
        # 导入并运行增强版修复工具
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from advanced_auto_fix import AdvancedImportFixer
        
        fixer = AdvancedImportFixer()
        results = fixer.fix_all_imports()
        
        if results["fixed"] > 0:
            print(f"✅ 自动修复完成，修复了 {results['fixed']} 个文件")
            return True
        else:
            print("⚠️ 未发现需要修复的问题")
            return False
    except Exception as e:
        print(f"❌ 自动修复时出错: {e}")
        return False

def start_chroma_server():
    """启动ChromaDB服务器"""
    print("🚀 启动ChromaDB服务器...")
    
    try:
        # 启动ChromaDB服务器作为后台进程
        chroma_process = subprocess.Popen(
            ["python", "start_chroma_server.py"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务器启动
        time.sleep(10)
        
        # 检查进程是否仍在运行
        if chroma_process.poll() is None:
            print("✅ ChromaDB服务器启动成功")
            return chroma_process
        else:
            # 获取错误输出
            stdout, stderr = chroma_process.communicate()
            print(f"❌ ChromaDB服务器启动失败: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动ChromaDB服务器时出错: {e}")
        return None

def start_uvicorn_server():
    """启动Uvicorn服务器"""
    print("🚀 启动Uvicorn服务器...")
    
    try:
        # 构建命令
        cmd = [
            "python", "-m", "uvicorn", 
            "src.services.main_api_server:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 启动Uvicorn服务器
        uvicorn_process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一点时间让服务器启动
        time.sleep(5)
        
        # 检查进程是否仍在运行
        if uvicorn_process.poll() is None:
            print("✅ Uvicorn服务器启动成功")
            return uvicorn_process
        else:
            # 获取错误输出
            stdout, stderr = uvicorn_process.communicate()
            print(f"❌ Uvicorn服务器启动失败: {stderr}")
            return None, stderr
            
    except Exception as e:
        print(f"❌ 启动Uvicorn服务器时出错: {e}")
        return None, str(e)

def run_dev_server():
    """运行开发服务器"""
    setup_environment()
    
    # 启动ChromaDB服务器
    chroma_process = start_chroma_server()
    
    # 启动Uvicorn服务器
    uvicorn_process, error_output = start_uvicorn_server()
    
    # 检查Uvicorn是否启动成功
    if uvicorn_process is None:
        print("❌ Uvicorn服务器启动失败")
        
        # 检测错误
        errors = detect_dev_errors(error_output, "")
        
        if errors:
            print(f"🔧 检测到错误: {errors}")
            
            # 运行自动修复
            if run_auto_fix():
                print("🔄 修复完成，重新启动开发服务器...")
                # 等待一下确保文件系统同步
                time.sleep(1)
                # 重新运行开发服务器
                return run_dev_server()
            else:
                print("❌ 自动修复失败")
                return 1
        else:
            print("❓ 未检测到可自动修复的错误")
            return 1
    else:
        print("✅ 开发服务器启动完成")
        # 等待服务器进程
        try:
            uvicorn_process.wait()
        except KeyboardInterrupt:
            print("🛑 正在停止服务器...")
            if chroma_process:
                chroma_process.terminate()
            uvicorn_process.terminate()
        return 0

def main():
    """主函数"""
    # 运行开发服务器
    exit_code = run_dev_server()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()