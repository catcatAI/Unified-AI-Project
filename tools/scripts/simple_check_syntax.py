#!/usr/bin/env python3
"""
简单检查项目中部分Python文件的语法
"""

import os
import sys
import subprocess
from pathlib import Path

def check_directory_syntax(dir_path):
    """检查指定目录下所有Python文件的语法"""
    print(f"检查目录: {dir_path}")
    
    error_files = []
    success_count = 0
    
    # 遍历目录中的所有.py文件
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    result = subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        success_count += 1
                        print(f"  ✓ {file_path}")
                    else:
                        error_files.append((file_path, result.stderr))
                        print(f"  ✗ {file_path}")
                except subprocess.TimeoutExpired:
                    error_files.append((file_path, "检查超时"))
                    print(f"  ⏱ {file_path} (超时)")
                except Exception as e:
                    error_files.append((file_path, str(e)))
                    print(f"  ✗ {file_path} ({e})")
    
    return success_count, error_files

def main():
    """主函数"""
    print("=== 简单语法检查 ===")
    
    # 检查几个关键目录
    directories = [
        ".",
        "tools/scripts",
        "tools/scripts/core",
        "tools/scripts/modules",
        "tools/scripts/utils",
        "cli/commands"
    ]
    
    all_errors = []
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            success, errors = check_directory_syntax(dir_path)
            all_errors.extend(errors)
            print(f"  成功: {success}, 错误: {len(errors)}\n")
    
    # 输出结果
    print(f"\n检查完成!")
    print(f"有语法错误的文件数量: {len(all_errors)}")
    
    if all_errors:
        print(f"\n有语法错误的文件:")
        for file_path, error in all_errors[:10]:  # 只显示前10个
            print(f"  ✗ {file_path}")
            # 只显示错误信息的前100个字符
            error_preview = error[:100] + "..." if len(error) > 100 else error
            print(f"    错误: {error_preview}")
        if len(all_errors) > 10:
            print(f"    ... 还有 {len(all_errors) - 10} 个文件")
    
    return len(all_errors)

if __name__ == "__main__":
    error_count = main()
    sys.exit(0 if error_count == 0 else 1)