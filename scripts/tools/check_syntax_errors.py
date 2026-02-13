#!/usr/bin/env python3
"""
检查Python文件语法错误的脚本
"""
import ast
import sys
from pathlib import Path

# 需要检查的目录列表
directories = [
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/memory",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/dialogue",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/formula_engine",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/meta_formulas",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/token",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/examples",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/cache",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/config",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/database",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/error",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/ethics",
    "/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/hsp",
]

# 单个文件
single_file = "/home/cat/桌面/Unified-AI-Project/apps/backend/src/config_loader.py"

files_with_errors = []
files_ok = []
files_too_large = []

MAX_FILE_SIZE = 100000  # 100KB

def check_syntax(file_path):
    """检查单个文件的语法"""
    try:
        # 检查文件大小
        file_size = Path(file_path).stat().st_size
        if file_size > MAX_FILE_SIZE:
            return False, "FILE_TOO_LARGE"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试解析为AST
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

# 检查所有目录中的Python文件
for directory in directories:
    dir_path = Path(directory)
    if dir_path.exists():
        for py_file in dir_path.rglob('*.py'):
            success, error = check_syntax(py_file)
            if success:
                files_ok.append(str(py_file))
            elif error == "FILE_TOO_LARGE":
                files_too_large.append(str(py_file))
            else:
                files_with_errors.append((str(py_file), error))

# 检查单个文件
if Path(single_file).exists():
    success, error = check_syntax(single_file)
    if success:
        files_ok.append(single_file)
    elif error == "FILE_TOO_LARGE":
        files_too_large.append(single_file)
    else:
        files_with_errors.append((single_file, error))

# 输出结果
print("=" * 80)
print("Python文件语法检查结果")
print("=" * 80)
print(f"\n总计检查文件数: {len(files_ok) + len(files_with_errors) + len(files_too_large)}")
print(f"✓ 无语法错误: {len(files_ok)} 个文件")
print(f"✗ 有语法错误: {len(files_with_errors)} 个文件")
print(f"⚠ 文件过大(跳过): {len(files_too_large)} 个文件")

if files_with_errors:
    print("\n" + "=" * 80)
    print("有语法错误的文件列表:")
    print("=" * 80)
    for file_path, error in files_with_errors:
        print(f"\n文件: {file_path}")
        print(f"错误: {error}")
        print("-" * 80)

if files_too_large:
    print("\n" + "=" * 80)
    print("文件过大(跳过检查):")
    print("=" * 80)
    for file_path in files_too_large:
        print(f"- {file_path}")

# 保存有错误的文件列表到文件
with open('/home/cat/桌面/syntax_errors_report.txt', 'w', encoding='utf-8') as f:
    f.write("Python文件语法检查报告\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"总计检查: {len(files_ok) + len(files_with_errors) + len(files_too_large)} 个文件\n")
    f.write(f"无错误: {len(files_ok)} 个文件\n")
    f.write(f"有错误: {len(files_with_errors)} 个文件\n")
    f.write(f"文件过大: {len(files_too_large)} 个文件\n\n")

    if files_with_errors:
        f.write("=" * 80 + "\n")
        f.write("有语法错误的文件:\n")
        f.write("=" * 80 + "\n\n")
        for file_path, error in files_with_errors:
            f.write(f"文件: {file_path}\n")
            f.write(f"错误: {error}\n\n")

print(f"\n详细报告已保存到: /home/cat/桌面/syntax_errors_report.txt")