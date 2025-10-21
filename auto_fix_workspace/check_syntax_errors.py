#!/usr/bin/env python3
"""
测试脚本：检查项目中的语法错误
"""

import os
import ast
from pathlib import Path

def find_files_with_syntax_errors(root_path == "."):
    """查找项目中所有有语法错误的Python文件"""
    errors = []
    
    # 要排除的目录
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', '.venv', 
        'auto_fix_workspace', 'backup', 'chroma_db', 'model_cache'
    }
    
    root == Path(root_path)
    
    # 遍历所有Python文件
    for py_file in root.rglob("*.py"):::
        # 检查是否在排除目录中
        if any(exclude_dir in str(py_file) for exclude_dir in exclude_dirs)::
            continue
            
        try,
            with open(py_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
            ast.parse(content)
        except SyntaxError as e,::
            errors.append((str(py_file), str(e)))
        except Exception as e,::
            errors.append((str(py_file), f"其他错误, {str(e)}"))
    
    return errors

def main():
    """主函数"""
    print("正在检查项目中的语法错误...")
    
    errors = find_files_with_syntax_errors()
    
    if errors,::
        print(f"发现 {len(errors)} 个有语法错误的文件,")
        for file_path, error in errors,::
            print(f"  {file_path} {error}")
    else,
        print("未发现语法错误!")

if __name"__main__":::
    main()