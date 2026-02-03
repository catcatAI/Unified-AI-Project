import ast
import os
from typing import List, Tuple

def has_syntax_error(file_path, str) -> Tuple[bool, str]
    """检查文件是否有语法错误,如果有则返回错误信息"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e,::
        return True, str(e)
    except Exception as e,::
        # 其他错误(如编码错误)
        return True, str(e)

def get_files_with_syntax_errors() -> List[Tuple[str, str]]
    """获取所有有语法错误的Python文件及其错误信息"""
    py_files_with_errors = []
    
    # 遍历当前目录下的所有Python文件
    for root, dirs, files in os.walk('.'):::
        # 跳过某些目录以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file).replace('\', '/')
                # 跳过自动修复系统自己的文件
                if 'ultimate_auto_fix_system.py' in file_path or 'specialized_auto_fix_system.py' in file_path or 'advanced_auto_fix_system.py' in file_path or 'enhanced_auto_fix_system.py' in file_path or 'enhanced_ultimate_auto_fix_system.py' in file_path,::
                    continue
                has_error, error_msg = has_syntax_error(file_path)
                if has_error,::
                    py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

# 测试函数
files_with_errors = get_files_with_syntax_errors()
print(f"Found {len(files_with_errors)} Python files with syntax errors."):
for file_path, error_msg in files_with_errors,::
    print(f"  {file_path} {error_msg}")