import os
import re
import ast
import subprocess
import traceback
from typing import List, Tuple

def is_valid_syntax(content: str) -> bool:
    """檢查代碼是否有有效的語法"""
    try:
        ast.parse(content)
        return True
    except SyntaxError as e:
        return False

def fix_indentation_issues(lines: List[str]) -> List[str]:
    """修復縮進問題"""
    fixed_lines = []
    indent_stack = [0]  # 跟踪縮進級別
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 跳過空行
        if not stripped:
            fixed_lines.append(line)
            continue
        
        # 計算當前行的縮進
        current_indent = len(line) - len(line.lstrip())
        
        # 處理不同的語句類型
        if stripped.startswith(('class ', 'def ', 'try:', 'except', 'else:', 'elif ')):
            # 這些語句開始新的塊
            if current_indent < indent_stack[-1]:
                # 縮進減少，調整堆棧
                while indent_stack and current_indent < indent_stack[-1]:
                    indent_stack.pop()
            indent_stack.append(current_indent)
        elif stripped.startswith(('if ', 'for ', 'while ')):
            # 控制流語句
            if current_indent < indent_stack[-1]:
                # 縮進減少，調整堆棧
                while indent_stack and current_indent < indent_stack[-1]:
                    indent_stack.pop()
            indent_stack.append(current_indent)
        elif stripped.endswith(':'):
            # 冒號表示新的塊開始
            indent_stack.append(current_indent + 4)
        
        fixed_lines.append(line)
    
    return fixed_lines

def fix_missing_colons(content: str) -> str:
    """修復缺少冒號的問題"""
    # 修復類定義缺少冒號的問題
    content = re.sub(r'(class\s+\w+\s*\([^)]*\))\s*\n', r'\1:\n', content)
    content = re.sub(r'(class\s+\w+)\s*\n', r'\1:\n', content)
    
    # 修復函數定義缺少冒號的問題
    content = re.sub(r'(def\s+\w+\s*\([^)]*\))\s*\n', r'\1:\n', content)
    
    # 修復控制流語句缺少冒號的問題
    content = re.sub(r'(if\s+.*?|for\s+.*?|while\s+.*?|try\s*|except\s*|else\s*|elif\s+.*?)\s*\n', r'\1:\n', content)
    
    return content

def fix_bracket_matching(content: str) -> str:
    """修復括號匹配問題"""
    # 移除多餘的右括號
    content = re.sub(r'(\s*\]\s*){2,}', ']\n', content)
    content = re.sub(r'(\s*\)\s*){2,}', ')\n', content)
    content = re.sub(r'(\s*\}\s*){2,}', '}\n', content)
    
    return content

def fix_file_syntax(file_path: str) -> bool:
    """修復文件中的語法錯誤"""
    print(f"Processing {file_path}...")
    
    # 嘗試不同的編碼
    encodings = ['utf-8', 'gbk', 'latin1']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"Error: Could not read {file_path} with any of the attempted encodings")
        return False
    
    original_content = content
    
    # 修復缺少冒號的問題
    content = fix_missing_colons(content)
    
    # 修復括號匹配問題
    content = fix_bracket_matching(content)
    
    # 修復縮進問題
    lines = content.split('\n')
    fixed_lines = fix_indentation_issues(lines)
    content = '\n'.join(fixed_lines)
    
    # 檢查修復後的語法
    if is_valid_syntax(content):
        # 如果內容有變化且語法正確，則寫入文件
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except Exception as e:
                print(f"Error writing to {file_path}: {e}")
                return False
        else:
            print(f"No issues found in {file_path}")
            return False
    else:
        print(f"Warning: Syntax fix for {file_path} resulted in invalid syntax, skipping...")
        return False

def get_modified_files() -> List[str]:
    """獲取所有修改過的Python文件"""
    try:
        # 使用git獲取修改過的文件
        result = subprocess.run(['git', 'diff', '--name-only'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        files = result.stdout.strip().split('\n')
        # 過濾出Python文件
        py_files = [f for f in files if f.endswith('.py') and os.path.exists(f)]
        return py_files
    except Exception as e:
        print(f"Error getting modified files: {e}")
        return []

def get_all_python_files() -> List[str]:
    """獲取項目中所有的Python文件"""
    py_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file).replace('\\', '/'))
    return py_files

def main():
    """主函數"""
    print("Starting complete automatic syntax fix...")
    
    # 獲取所有Python文件（不僅僅是修改過的）
    all_py_files = get_all_python_files()
    
    print(f"Found {len(all_py_files)} Python files in the project.")
    
    # 修復每個文件
    fixed_count = 0
    for file_path in all_py_files:
        try:
            if fix_file_syntax(file_path):
                fixed_count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Complete automatic syntax fix completed.")

if __name__ == "__main__":
    main()