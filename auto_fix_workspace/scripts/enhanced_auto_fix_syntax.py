import os
import re
import subprocess
import ast
import sys
from typing import List, Tuple

def fix_indentation_issues(lines: List[str]) -> List[str]:
    """修復縮進問題"""
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

def fix_common_syntax_errors(content: str) -> str:
    """修復常見的語法錯誤"""
    # 保存原始內容
    original_content = content
    
    # 修復函數調用後面的冒號問題
    # 例如: logger.info("message"):
    content = re.sub(r'(\w+\s*\([^)]*\))\s*:', r'\1', content)
    
    # 修復 super() 調用
    content = re.sub(r'super\s*\.', 'super().', content)
    content = re.sub(r'super\s*\(\s*\)\s*:', 'super()', content)
    
    # 修復函數調用後的括號問題
    content = re.sub(r'(\w+)\s*\(\s*\)\s*:', r'\1()', content)
    content = re.sub(r'(\w+)\s*\(\s*([^)]*)\s*\)\s*:', r'\1(\2)', content)
    
    # 修復類型註解中的問題
    content = re.sub(r'(\w+)\s*:\s*Any\s*:', r'\1: Any', content)
    content = re.sub(r'(\w+)\s*:\s*str\s*:', r'\1: str', content)
    content = re.sub(r'(\w+)\s*:\s*int\s*:', r'\1: int', content)
    content = re.sub(r'(\w+)\s*:\s*bool\s*:', r'\1: bool', content)
    content = re.sub(r'(\w+)\s*:\s*Dict\[.*?\]\s*:', r'\1: Dict[…]', content)
    content = re.sub(r'(\w+)\s*:\s*List\[.*?\]\s*:', r'\1: List[…]', content)
    
    # 修復註釋中的冒號
    content = re.sub(r'(#.*)\s*:', r'\1', content)
    
    # 修復函數定義中的錯誤
    content = re.sub(r'def\s+(\w+)\s*\(\s*\):\s*:', r'def \1():', content)
    
    # 修復類定義中的錯誤
    content = re.sub(r'class\s+(\w+)\s*:\s*:', r'class \1:', content)
    
    # 修復異步函數定義
    content = re.sub(r'async\s+def\s+(\w+)\s*\(\s*\):\s*:', r'async def \1():', content)
    
    # 修復異步for循環
    content = re.sub(r'async\s+for\s+(.+?):\s*:', r'async for \1:', content)
    
    # 修復異步with語句
    content = re.sub(r'async\s+with\s+(.+?):\s*:', r'async with \1:', content)
    
    # 修復try語句
    content = re.sub(r'try\s*:\s*:', r'try:', content)
    
    # 修復if語句
    content = re.sub(r'if\s+(.+?):\s*:', r'if \1:', content)
    
    # 修復for語句
    content = re.sub(r'for\s+(.+?):\s*:', r'for \1:', content)
    
    # 修復while語句
    content = re.sub(r'while\s+(.+?):\s*:', r'while \1:', content)
    
    # 修復with語句
    content = re.sub(r'with\s+(.+?):\s*:', r'with \1:', content)
    
    return content

def fix_trailing_commas(content: str) -> str:
    """修復行尾逗號問題"""
    # 修復函數調用中的行尾逗號問題
    content = re.sub(r'\)\s*,\s*:', ')', content)
    
    # 修復列表和字典中的行尾逗號問題
    content = re.sub(r'\]\s*,\s*:', ']', content)
    content = re.sub(r'\}\s*,\s*:', '}', content)
    
    # 修復參數列表中的行尾逗號問題
    content = re.sub(r'(\w+)\s*\([^)]*\)\s*,\s*:', r'\1()', content)
    
    return content

def validate_syntax(content: str) -> Tuple[bool, str]:
    """驗證Python語法是否正確"""
    try:
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Other error: {str(e)}"

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
        
        # 修復常見語法錯誤
        content = fix_common_syntax_errors(content)
        
        # 修復行尾逗號問題
        content = fix_trailing_commas(content)
        
        # 修復縮進問題
        lines = content.split('\n')
        fixed_lines = fix_indentation_issues(lines)
        content = '\n'.join(fixed_lines)
        
        # 驗證修復後的語法
        is_valid, error_msg = validate_syntax(content)
        if not is_valid:
            print(f"Warning: Syntax error after fixing {file_path}: {error_msg}")
            # 如果修復後引入了新的語法錯誤，則不保存更改
            return False
        
        # 如果內容有變化，則寫入文件
        if content != original_content:
            # 使用與讀取時相同的編碼寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed syntax issues in {file_path}")
            return True
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