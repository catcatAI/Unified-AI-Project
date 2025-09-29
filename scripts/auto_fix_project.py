#!/usr/bin/env python3
"""
一键修复脚本 - 适应新的目录结构
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def check_virtual_environment():
    """检查虚拟环境"""
    if not Path("venv").exists():
        _ = print("创建虚拟环境...")
        _ = subprocess.run([sys.executable, "-m", "venv", "venv"])

def activate_virtual_environment():
    """激活虚拟环境"""
    if os.name == "nt":  # Windows
        python_executable = Path("venv") / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        python_executable = Path("venv") / "bin" / "python"
    
    # 检查虚拟环境的Python是否存在
    if python_executable.exists():
        return str(python_executable)
    else:
        _ = print("⚠ 虚拟环境Python不存在，使用系统Python")
        return sys.executable

def update_pip(python_executable):
    """更新pip"""
    _ = print("更新pip...")
    _ = subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_dependencies(python_executable):
    """安装依赖"""
    _ = print("安装依赖...")
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
            _ = print(f"Installing from {req_file}...")
            _ = subprocess.run([python_executable, "-m", "pip", "install", "-r", req_file])

def check_dependency_conflicts(python_executable):
    """检查依赖冲突"""
    _ = print("检查依赖冲突...")
    try:
        result = subprocess.run([python_executable, "-m", "pip", "check"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            _ = print("✓ 依赖检查通过")
        else:
            _ = print(f"⚠ 依赖检查发现问题: {result.stdout}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        _ = print(f"⚠ 依赖检查失败: {e}")
        _ = print("建议手动运行: pip check")

def check_env_vars(python_executable):
    """检查环境变量"""
    _ = print("检查环境变量...")
    script_path = Path(__file__).parent / "check_env_vars.py"
    if script_path.exists():
        _ = subprocess.run([python_executable, str(script_path)])
    else:
        _ = print("未找到环境变量检查脚本")

def run_enhanced_auto_fix(python_executable):
    """运行增强版自动修复工具"""
    _ = print("运行增强版自动修复工具...")
    script_path = Path(__file__).parent / "enhanced_auto_fix.py"
    if script_path.exists():
        result = subprocess.run([python_executable, str(script_path), "--all"])
        if result.returncode == 0:
            _ = print("✓ 增强版自动修复完成")
        else:
            _ = print("✗ 增强版自动修复失败")
    else:
        _ = print("未找到增强版自动修复工具")

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description='项目自动修复脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python auto_fix_project.py --help          显示帮助信息
  python auto_fix_project.py --check         仅检查环境，不执行修复
  python auto_fix_project.py --fix           执行完整修复流程
  python auto_fix_project.py --deps-only     仅安装依赖
        """
    )
    
    parser.add_argument('--check', action='store_true',
                       help='仅检查环境状态，不执行修复')
    parser.add_argument('--fix', action='store_true',
                       help='执行完整的修复流程')
    parser.add_argument('--deps-only', action='store_true',
                       help='仅安装和检查依赖')
    parser.add_argument('--skip-venv', action='store_true',
                       help='跳过虚拟环境检查')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，默认执行完整修复
    if not any([args.check, args.fix, args.deps_only]):
        args.fix = True
    
    try:
        _ = print("开始修复项目常见问题...")
        
        # 检查并创建虚拟环境
        if not args.skip_venv:
            _ = check_virtual_environment()
            python_executable = activate_virtual_environment()
        else:
            python_executable = sys.executable
        
        if args.check:
            _ = print("执行环境检查...")
            _ = check_dependency_conflicts(python_executable)
            _ = check_env_vars(python_executable)
            _ = print("环境检查完成!")
            return
        
        if args.deps_only or args.fix:
            # 更新pip
            _ = update_pip(python_executable)
            # 安装依赖
            _ = install_dependencies(python_executable)
            # 检查依赖冲突
            _ = check_dependency_conflicts(python_executable)
        
        if args.fix:
            # 检查环境变量
            _ = check_env_vars(python_executable)
            # 运行增强版自动修复工具
            _ = run_enhanced_auto_fix(python_executable)
        
        _ = print("修复完成!")
        
    except KeyboardInterrupt:
        _ = print("\n用户中断操作")
        _ = sys.exit(1)
    except Exception as e:
        _ = print(f"修复过程中出现错误: {e}")
        if args.verbose:
            import traceback
            _ = traceback.print_exc()
        _ = sys.exit(1)

if __name__ == "__main__":
    _ = main()