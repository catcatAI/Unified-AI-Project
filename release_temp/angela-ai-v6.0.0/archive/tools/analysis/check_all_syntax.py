#!/usr/bin/env python3
"""
全面语法检查脚本
检查项目中所有Python文件的语法正确性
"""

import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """检查单个文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    project_root = Path(__file__).parent
    python_files = list(project_root.rglob("*.py"))
    
    errors = []
    total_files = len(python_files)
    
    print(f"开始检查 {total_files} 个Python文件的语法...")
    
    for i, py_file in enumerate(python_files, 1):
        is_valid, error_msg = check_syntax(py_file)
        if not is_valid:
            errors.append((py_file, error_msg))
            print(f"❌ {py_file.relative_to(project_root)}: {error_msg}")
        else:
            print(f"✅ {py_file.relative_to(project_root)}")
        
        # 显示进度
        if i % 100 == 0 or i == total_files:
            print(f"进度: {i}/{total_files} ({i/total_files*100:.1f}%)")
    
    print(f"\n检查完成!")
    print(f"总文件数: {total_files}")
    print(f"错误文件数: {len(errors)}")
    print(f"正确文件数: {total_files - len(errors)}")
    print(f"成功率: {(total_files - len(errors)) / total_files * 100:.2f}%")
    
    if errors:
        print(f"\n存在语法错误的文件:")
        for file_path, error in errors:
            print(f"  - {file_path.relative_to(project_root)}: {error}")
        return 1
    else:
        print(f"\n🎉 恭喜! 所有Python文件语法正确!")
        return 0

if __name__ == "__main__":
    sys.exit(main())