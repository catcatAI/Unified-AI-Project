import os
import re
import ast
import traceback
from typing import List, Tuple

def has_syntax_error(file_path: str) -> Tuple[bool, str]:
    """檢查文件是否有語法錯誤，如果有則返回錯誤信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e:
        return True, str(e)
    except Exception as e:
        # 其他錯誤（如編碼錯誤）
        return True, str(e)

def get_files_with_syntax_errors() -> List[Tuple[str, str]]:
    """獲取所有有語法錯誤的Python文件及其錯誤信息"""
    py_files_with_errors = []
    
    # 遍歷當前目錄下的所有Python文件
    for root, dirs, files in os.walk('.'):
        # 跳過某些目錄以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file).replace('\\', '/')
                has_error, error_msg = has_syntax_error(file_path)
                if has_error:
                    py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

def fix_missing_colons_only(content: str) -> str:
    """只修復缺少冒號的問題，不處理其他問題"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # 跳過空行和註釋行
        if not stripped_line or stripped_line.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 修復類定義缺少冒號的問題
        if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line):
            # 確保整行只有類定義，沒有其他內容
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
            print(f"  Fixed class definition missing colon on line {i+1}")
            continue
        
        # 修復函數定義缺少冒號的問題
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line):
            # 確保整行只有函數定義，沒有其他內容
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
            print(f"  Fixed function definition missing colon on line {i+1}")
            continue
        
        # 修復控制流語句缺少冒號的問題
        control_flow_patterns = [
            r'^\s*if\s+.*$',
            r'^\s*elif\s+.*$',
            r'^\s*else\s*$',
            r'^\s*for\s+.*$',
            r'^\s*while\s+.*$',
            r'^\s*try\s*$',
            r'^\s*except\s*.*$',
            r'^\s*finally\s*$',
            r'^\s*with\s+.*$'
        ]
        
        is_control_flow = False
        for pattern in control_flow_patterns:
            if re.match(pattern, stripped_line) and not stripped_line.endswith(':'):
                is_control_flow = True
                break
        
        if is_control_flow:
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
            print(f"  Fixed control flow statement missing colon on line {i+1}")
            continue
        
        # 保持其他行不變
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def specialized_fix_file(file_path: str) -> bool:
    """專門修復文件中的缺少冒號問題"""
    try:
        # 讀取原始內容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 創建內容副本進行修改
        content = original_content
        
        # 只修復缺少冒號的問題
        content = fix_missing_colons_only(content)
        
        # 只有在內容有變化時才寫入文件
        if content != original_content:
            # 驗證修復後的語法
            try:
                ast.parse(content)
                # 語法正確，寫入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except SyntaxError as e:
                # 修復後仍有語法錯誤，不寫入文件
                print(f"Warning: Fix for {file_path} resulted in invalid syntax, skipped")
                return False
        else:
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("Starting specialized automatic syntax fix...")
    
    # 獲取所有有語法錯誤的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors:
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修復每個文件
    fixed_count = 0
    for file_path, error_msg in files_with_errors:
        # 只處理缺少冒號的錯誤
        if "expected ':'" in error_msg:
            print(f"Processing {file_path}...")
            print(f"  Error: {error_msg}")
            try:
                if specialized_fix_file(file_path):
                    fixed_count += 1
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Specialized automatic syntax fix completed.")

if __name__ == "__main__":
    main()