#!/usr/bin/env python3
"""
_ = 智能測試運行器 - 在運行測試時自動檢測和修復錯誤 (兼容模式)
此腳本已更新為使用新的分離架構，建議使用 workflow_controller.py
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

def detect_test_errors(stderr_output: str, stdout_output: str) -> "List[str]":
    """检测测试错误"""
    errors = []
    
    # 合并输出
    full_output = (stdout_output or "") + (stderr_output or "")
    
    # 检测导入错误
    import_error_patterns = [
        _ = r"ModuleNotFoundError: No module named '([^']+)'",
        _ = r"ImportError: cannot import name '([^']+)'",
        _ = r"ImportError: No module named '([^']+)'",
        _ = r"NameError: name '([^']+)' is not defined",
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
            
    return errors

def run_auto_fix():
    """运行自动修复工具"""
    print("🔍 检测到导入错误，正在自动修复...")
    
    try:
        # 导入并运行增强版修复工具
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from apps.backend.scripts.advanced_auto_fix import AdvancedImportFixer
        
        fixer = AdvancedImportFixer()
        fixer.fix_all_files()
        # 返回一个模拟的结果字典以保持接口一致性
        results = {
            "fixed": len(fixer.fix_report.fixed_files),
            "errors": len(fixer.fix_report.errors)
        }
        
        if results["fixed"] > 0:
            print(f"✅ 自动修复完成，修复了 {results['fixed']} 个文件")
            return True
        else:
            print("⚠️ 未发现需要修复的问题")
            return False
    except Exception as e:
        print(f"❌ 自动修复时出错: {e}")
        return False

def run_tests(pytest_args=None) -> None:
    """运行测试"""
    print("==========================================")
    print("Unified AI Project 智能测试运行器 (兼容模式)")
    print("==========================================")
    print("注意: 此脚本已更新为使用新的分离架构，建议使用 workflow_controller.py")
    
    setup_environment()
    
    # 构建命令
    cmd = ["python", "-m", "pytest", "--tb=short", "-v"]
    if pytest_args:
        cmd.extend(pytest_args.split())
    
    print(f"🚀 运行测试命令: {' '.join(cmd)}")
    
    try:
        # 执行测试，设置较长时间的超时（例如1800秒=30分钟）
        # 注意：这里我们不设置subprocess的timeout参数，让测试自然运行
        # 但我们在外部监控进程状态
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 获取输出
        stdout, stderr = process.communicate()
        
        # 显示输出
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        
        # 检查是否有错误
        if process.returncode != 0:
            print(f"❌ 测试执行失败 (退出码: {process.returncode})")
            
            # 检测导入错误
            errors = detect_test_errors(stderr, stdout)
            
            if errors:
                print(f"🔧 检测到错误: {errors}")
                
                # 运行自动修复
                if run_auto_fix():
                    print("🔄 修复完成，重新运行测试...")
                    # 等待一下确保文件系统同步
                    time.sleep(1)
                    # 重新运行测试
                    return run_tests(pytest_args)
                else:
                    print("❌ 自动修复失败")
                    return process.returncode
            else:
                print("❓ 未检测到可自动修复的错误")
                return process.returncode
        else:
            print("✅ 所有测试通过")
            return 0
            
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return 1

def main() -> None:
    """主函数"""
    # 获取pytest参数
    pytest_args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    # 运行测试
    exit_code = run_tests(pytest_args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()