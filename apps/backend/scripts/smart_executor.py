#!/usr/bin/env python3
"""
智能执行器 - 在执行命令时自动检测错误并调用修复工具
"""

import sys
import subprocess
import re
from pathlib import Path
from typing import List
import logging
logger = logging.getLogger(__name__)

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

def detect_import_errors(stderr_output: str) -> List[str]:
    """检测导入错误"""
    import_error_patterns = [
        r"ModuleNotFoundError, No module named '(\w+)'",
        r"ImportError, cannot import name '(\w+)'",
        r"ImportError, No module named '(\w+)'",
        r"NameError, name '(\w+)' is not defined",
    ]

    for pattern in import_error_patterns:
        matches = re.findall(pattern, stderr_output)
        if matches:
            return matches
    return []

def detect_path_errors(stderr_output: str) -> bool:
    """检测路径错误"""
    path_error_patterns = [
        r"No module named 'core_ai",
        r"No module named 'hsp",
        r"from \.\.core_ai",
    ]

    for pattern in path_error_patterns:
        if re.search(pattern, stderr_output):
            return True
    return False

def run_auto_fix():
    """运行自动修复工具"""
    print("🔍 检测到导入错误,正在自动修复...")

    try:
        print("⚠️ advanced_auto_fix 模块不存在,跳过自动修复")
        return False
    except Exception as e:
        print(f"❌ 自动修复时出错, {e}")
        return False

def execute_command(command, auto_fix=True):
    """执行命令并处理错误"""
    print(f"🚀 执行命令, {command}")

    try:
        # 执行命令
        process = subprocess.Popen(
            command,
shell = True,
cwd = PROJECT_ROOT,
    stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
text = True,
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
            print(f"❌ 命令执行失败 (退出码, {process.returncode})")

            # 如果启用了自动修复,检测是否是导入错误
            if auto_fix:
                # 检测导入错误
                import_errors = detect_import_errors(stderr)
                path_errors = detect_path_errors(stderr)

                if import_errors or path_errors:
                    print("🔧 检测到导入路径错误,准备自动修复...")

                    # 运行自动修复
                    if run_auto_fix():
                        print("🔄 修复完成,重新执行命令...")
                        return execute_command(command, auto_fix=False)
                    else:
                        print("❌ 自动修复失败")
                        return process.returncode
                else:
                    print("❓ 未检测到可自动修复的导入错误")
            return process.returncode
        else:
            print("✅ 命令执行成功")
            return 0

    except Exception as e:
        print(f"❌ 执行命令时出错, {e}")
        return 1

def main() -> None:
    """主函数"""
    setup_environment()

    if len(sys.argv) < 2:
        print("用法, python smart_executor.py <command> [--no-fix]")
        sys.exit(1)

    command = sys.argv[1]
    auto_fix = "--no-fix" not in sys.argv
    # 执行命令
    exit_code = execute_command(command, auto_fix)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()