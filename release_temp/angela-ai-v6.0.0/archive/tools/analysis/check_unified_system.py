#!/usr/bin/env python3
"""
检查统一自动修复系统目录中的Python文件语法错误
"""

import os
import sys
import subprocess
from pathlib import Path

def check_syntax_errors_in_dir(directory: str) -> list:
    """检查指定目录下所有Python文件的语法错误"""
    error_files = []
    
    # 遍历目录中的所有Python文件
    for py_file in Path(directory).rglob("*.py"):
        try:
            # 使用Python编译器检查语法
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果返回码不为0，说明有语法错误
            if result.returncode != 0:
                error_files.append((py_file, result.stderr))
                print(f"❌ 语法错误: {py_file}")
                print(f"   错误详情: {result.stderr}")
            else:
                print(f"✅ 语法正确: {py_file}")
                
        except subprocess.TimeoutExpired:
            error_files.append((py_file, "检查超时"))
            print(f"⏰ 检查超时: {py_file}")
        except Exception as e:
            error_files.append((py_file, str(e)))
            print(f"⚠️  检查异常: {py_file}, 错误: {e}")
    
    return error_files

def main():
    """主函数"""
    print("开始检查统一自动修复系统中的Python文件语法错误...")
    print("=" * 60)
    
    # 检查统一自动修复系统目录
    unified_system_dir = "unified_auto_fix_system"
    if Path(unified_system_dir).exists():
        print(f"\n检查目录: {unified_system_dir}")
        errors = check_syntax_errors_in_dir(unified_system_dir)
        
        print(f"\n" + "=" * 60)
        if errors:
            print(f"在 {unified_system_dir} 中发现 {len(errors)} 个文件存在语法错误:")
            for file_path, error_msg in errors:
                print(f"\n  ❌ {file_path}")
                if error_msg:
                    print(f"     错误: {error_msg}")
        else:
            print(f"\n🎉 恭喜！{unified_system_dir} 中的所有Python文件都没有语法错误。")
    else:
        print(f"目录 {unified_system_dir} 不存在")

if __name__ == "__main__":
    main()