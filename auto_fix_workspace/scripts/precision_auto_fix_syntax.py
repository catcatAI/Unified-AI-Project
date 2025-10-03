import os
import re
import subprocess
import ast
import sys
import tempfile
import shutil
from typing import List, Tuple, Optional

def validate_syntax(content: str) -> Tuple[bool, str]:
    """驗證Python語法是否正確"""
    try:
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {str(e)}"
    except Exception as e:
        return False, f"Other error: {str(e)}"

def fix_line_syntax(line: str) -> str:
    """修復單行語法錯誤"""
    # 修復函數定義缺少冒號的問題
    line = re.sub(r'def\s+(\w+)\s*\(([^)]*)\)\s*$', r'def \1(\2):', line)
    
    # 修復類定義缺少冒號的問題
    line = re.sub(r'class\s+(\w+)\s*$', r'class \1:', line)
    
    # 修復for循環缺少冒號的問題
    line = re.sub(r'for\s+(.+?)\s*$', r'for \1:', line)
    
    # 修復if語句缺少冒號的問題
    line = re.sub(r'if\s+(.+?)\s*$', r'if \1:', line)
    
    # 修復while語句缺少冒號的問題
    line = re.sub(r'while\s+(.+?)\s*$', r'while \1:', line)
    
    # 修復else語句缺少冒號的問題
    line = re.sub(r'else\s*$', r'else:', line)
    
    # 修復elif語句缺少冒號的問題
    line = re.sub(r'elif\s+(.+?)\s*$', r'elif \1:', line)
    
    # 修復try語句缺少冒號的問題
    line = re.sub(r'try\s*$', r'try:', line)
    
    # 修復with語句缺少冒號的問題
    line = re.sub(r'with\s+(.+?)\s*$', r'with \1:', line)
    
    # 修復except語句缺少冒號的問題
    line = re.sub(r'except\s*$', r'except:', line)
    line = re.sub(r'except\s+(.+?)\s*$', r'except \1:', line)
    
    # 修復finally語句缺少冒號的問題
    line = re.sub(r'finally\s*$', r'finally:', line)
    
    # 修復async def語句缺少冒號的問題
    line = re.sub(r'async\s+def\s+(\w+)\s*\(([^)]*)\)\s*$', r'async def \1(\2):', line)
    
    # 修復async for語句缺少冒號的問題
    line = re.sub(r'async\s+for\s+(.+?)\s*$', r'async for \1:', line)
    
    # 修復async with語句缺少冒號的問題
    line = re.sub(r'async\s+with\s+(.+?)\s*$', r'async with \1:', line)
    
    return line

def fix_indentation_line_by_line(lines: List[str]) -> List[str]:
    """逐行修復縮進問題"""
    fixed_lines = []
    indent_stack = [0]  # 跟蹤縮進層級
    
    for i, line in enumerate(lines):
        # 移除行尾的多餘空格
        line = line.rstrip()
        
        if not line:
            fixed_lines.append(line)
            continue
            
        # 計算當前行的縮進空格數
        current_indent = len(line) - len(line.lstrip(' '))
        
        # 檢查是否是語句開始關鍵字
        stripped_line = line.lstrip()
        is_block_starter = any(stripped_line.startswith(keyword) for keyword in [
            'class ', 'def ', 'if ', 'for ', 'while ', 'try:', 'except', 'else:', 'elif ', 'with ', 'match ', 'case '
        ])
        
        is_block_ender = any(stripped_line.startswith(keyword) for keyword in [
            'else:', 'elif ', 'except', 'finally:'
        ])
        
        # 調整縮進
        if is_block_starter and not is_block_ender:
            # 對於塊開始語句，確保縮進是4的倍數
            corrected_indent = (current_indent // 4) * 4
            indent_stack.append(corrected_indent + 4)
            line = ' ' * corrected_indent + stripped_line
        elif is_block_ender:
            # 對於塊結束語句，使用上一層的縮進
            if len(indent_stack) > 1:
                indent_stack.pop()
            corrected_indent = indent_stack[-1] if indent_stack else 0
            line = ' ' * corrected_indent + stripped_line
        else:
            # 對於普通語句，使用當前塊的縮進
            expected_indent = indent_stack[-1] if indent_stack else 0
            # 只在明顯錯誤時調整縮進
            if abs(current_indent - expected_indent) >= 4 and current_indent % 4 != 0:
                line = ' ' * expected_indent + stripped_line
        
        fixed_lines.append(line)
    
    return fixed_lines

def fix_file_syntax(file_path: str) -> bool:
    """修復文件中的語法錯誤和縮進問題"""
    print(f"Processing {file_path}...")
    
    try:
        # 讀取文件內容，嘗試不同的編碼
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        content = None
        last_error = ""
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError as e:
                last_error = str(e)
                continue
        
        if content is None:
            print(f"Error reading {file_path}: {last_error}")
            return False
        
        # 保存原始內容
        original_content = content
        
        # 逐行修復語法錯誤
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 修復單行語法錯誤
            fixed_line = fix_line_syntax(line)
            fixed_lines.append(fixed_line)
        
        # 逐行修復縮進問題
        fixed_lines = fix_indentation_line_by_line(fixed_lines)
        
        # 組合修復後的內容
        fixed_content = '\n'.join(fixed_lines)
        
        # 如果內容有變化且語法正確，則寫入文件
        if fixed_content != original_content:
            # 驗證修復後的語法
            is_valid, error_msg = validate_syntax(fixed_content)
            if is_valid:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed syntax issues in {file_path}")
                return True
            else:
                print(f"Warning: Syntax error after fixing {file_path}: {error_msg}")
                return False
        else:
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def get_modified_files() -> List[str]:
    """獲取所有修改過的Python文件"""
    try:
        # 使用git獲取修改過的文件
        result = subprocess.run(['git', 'diff', '--name-only'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        files = result.stdout.strip().split('\n')
        # 過濾出Python文件並確保文件存在
        py_files = [f for f in files if f.endswith('.py') and os.path.exists(f)]
        return py_files
    except Exception as e:
        print(f"Error getting modified files: {e}")
        return []

def get_all_python_files() -> List[str]:
    """獲取項目中所有的Python文件"""
    try:
        # 使用git獲取所有Python文件
        result = subprocess.run(['git', 'ls-files', '*.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        files = result.stdout.strip().split('\n')
        # 確保文件存在
        py_files = [f for f in files if os.path.exists(f)]
        return py_files
    except Exception as e:
        print(f"Error getting all Python files: {e}")
        return []

def main():
    """主函數"""
    print("Starting automatic syntax fix...")
    
    # 獲取所有修改過的Python文件
    modified_files = get_modified_files()
    
    if not modified_files:
        print("No modified Python files found. Checking all Python files...")
        # 如果沒有修改過的文件，則檢查所有Python文件
        modified_files = get_all_python_files()
    
    if not modified_files:
        print("No Python files found.")
        return
    
    print(f"Found {len(modified_files)} Python files.")
    
    # 修復每個文件
    fixed_count = 0
    error_count = 0
    
    for file_path in modified_files:
        try:
            if fix_file_syntax(file_path):
                fixed_count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            error_count += 1
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    if error_count > 0:
        print(f"Encountered errors in {error_count} files.")
    print("Automatic syntax fix completed.")

if __name__ == "__main__":
    main()