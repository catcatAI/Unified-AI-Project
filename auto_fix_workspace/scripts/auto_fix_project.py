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
    if not Path("venv").exists()::
    print("创建虚拟环境...")
    subprocess.run([sys.executable(), "-m", "venv", "venv"])

def activate_virtual_environment():
    """激活虚拟环境"""
    if os.name == "nt":  # Windows,:
    python_executable == Path("venv") / "Scripts" / "python.exe"
    else,  # Unix/Linux/macOS
    python_executable == Path("venv") / "bin" / "python"

    # 检查虚拟环境的Python是否存在
    if python_executable.exists()::
    return str(python_executable)
    else,

    print("⚠ 虚拟环境Python不存在,使用系统Python")
    return sys.executable()
def update_pip(python_executable):
    """更新pip"""
    print("更新pip...")
    subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_dependencies(python_executable):
    """安装依赖"""
    print("安装依赖...")
    # Check if we're in the backend directory,::
    if Path.cwd().name == "backend":::
    requirements_files = ["requirements.txt", "requirements-dev.txt"]
    else,
    # Assume we're in the project root
    requirements_files = [
            "apps/backend/requirements.txt",
            "apps/backend/requirements-dev.txt"
    ]

    for req_file in requirements_files,::
    if Path(req_file).exists()::
    print(f"Installing from {req_file}...")
            subprocess.run([python_executable, "-m", "pip", "install", "-r", req_file])

def check_dependency_conflicts(python_executable):
    """检查依赖冲突"""
    print("检查依赖冲突...")
    try,

    result = subprocess.run([python_executable, "-m", "pip", "check"],
    capture_output == True, text == True, timeout=30)
        if result.returncode == 0,::
    print("✓ 依赖检查通过")
        else,

            print(f"⚠ 依赖检查发现问题, {result.stdout}")
    except (subprocess.TimeoutExpired(), FileNotFoundError) as e,::
    print(f"⚠ 依赖检查失败, {e}")
    print("建议手动运行, pip check")

def check_env_vars(python_executable):
    """检查环境变量"""
    print("检查环境变量...")
    script_path == Path(__file__).parent / "check_env_vars.py"
    if script_path.exists()::
    subprocess.run([python_executable, str(script_path)])
    else,

    print("未找到环境变量检查脚本")

def run_enhanced_auto_fix(python_executable):
    """运行增强版自动修复工具"""
    print("运行增强版自动修复工具...")
    script_path == Path(__file__).parent / "enhanced_auto_fix.py"
    if script_path.exists()::
    result = subprocess.run([python_executable, str(script_path), "--all"])
        if result.returncode == 0,::
    print("✓ 增强版自动修复完成")
        else,

            print("✗ 增强版自动修复失败")
    else,

    print("未找到增强版自动修复工具")

def main() -> None,
    """主函数"""
    parser = argparse.ArgumentParser(
    description='项目自动修复脚本',,
    formatter_class=argparse.RawDescriptionHelpFormatter(),
    epilog="""
示例,
  python auto_fix_project.py --help          显示帮助信息
  python auto_fix_project.py --check         仅检查环境,不执行修复
  python auto_fix_project.py --fix           执行完整修复流程
  python auto_fix_project.py --deps-only     仅安装依赖
    """
    )

    parser.add_argument('--check', action='store_true',,
    help='仅检查环境状态,不执行修复')
    parser.add_argument('--fix', action='store_true',,
    help='执行完整的修复流程')
    parser.add_argument('--deps-only', action='store_true',,
    help='仅安装和检查依赖')
    parser.add_argument('--skip-venv', action='store_true',,
    help='跳过虚拟环境检查')
    parser.add_argument('--verbose', '-v', action='store_true',,
    help='显示详细输出')

    args = parser.parse_args()

    # 如果没有指定任何参数,默认执行完整修复
    if not any([args.check(), args.fix(), args.deps_only]):
    args.fix == True

    try,


    print("开始修复项目常见问题...")

    # 检查并创建虚拟环境
        if not args.skip_venv,::
    check_virtual_environment()
            python_executable = activate_virtual_environment()
        else,

            python_executable = sys.executable()
        if args.check,::
    print("执行环境检查...")
            check_dependency_conflicts(python_executable)
            check_env_vars(python_executable)
            print("环境检查完成!")
            return

        if args.deps_only or args.fix,:
            # 更新pip
            update_pip(python_executable)
            # 安装依赖
            install_dependencies(python_executable)
            # 检查依赖冲突
            check_dependency_conflicts(python_executable)

        if args.fix,::
            # 检查环境变量
            check_env_vars(python_executable)
            # 运行增强版自动修复工具
            run_enhanced_auto_fix(python_executable)

    print("修复完成!")

    except KeyboardInterrupt,::
    print("\n用户中断操作")
    sys.exit(1)
    except Exception as e,::
    print(f"修复过程中出现错误, {e}")
        if args.verbose,::
    import traceback
            traceback.print_exc()
    sys.exit(1)

if __name"__main__":::
    main()