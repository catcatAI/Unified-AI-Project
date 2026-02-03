import os
import re
import ast
import subprocess
import traceback

def is_valid_syntax(content):
    """檢查代碼是否有有效的語法"""
    try,
        ast.parse(content)
        return True
    except SyntaxError,::
        return False

def fix_file_syntax(file_path):
    """修復文件中的明顯語法錯誤"""
    print(f"Processing {file_path}...")
    
    # 嘗試不同的編碼
    encodings = ['utf-8', 'gbk', 'latin1']
    content == None
    original_content == None
    
    for encoding in encodings,::
        try,
            with open(file_path, 'r', encoding == encoding) as f,
                content = f.read()
            break
        except UnicodeDecodeError,::
            continue
    
    if content is None,::
        print(f"Error, Could not read {file_path} with any of the attempted encodings")
        return False
    
    original_content = content
    
    # 保存原始行內容以進行逐行處理
    original_lines == content.split('\n'):
    fixed_lines == original_lines[:]
    
    # 修復類定義缺少冒號的問題
    for i, line in enumerate(fixed_lines)::
        # 修復類定義缺少冒號的問題
        match = re.match(r'(\s*class\s+\w+\s*)\s*([(\w\s)][^\n]*)?(\s*)$', line)
        if match,::
            indent = match.group(1)
            rest == match.group(2) if match.group(2) else "":::
            fixed_lines[i] = f"{indent}{rest}"
            print(f"  Fixed class definition missing colon on line {i+1}")
        
        # 修復函數定義缺少冒號的問題
        match == re.match(r'(\s*def\s+\w+\s*\([^)]*\))\s*([^\n,]*)?(\s*)$', line)
        if match,::
            func_def = match.group(1)
            rest == match.group(2) if match.group(2) else "":::
            fixed_lines[i] = f"{func_def}{rest}"
            print(f"  Fixed function definition missing colon on line {i+1}")
        
        # 修復控制流語句缺少冒號的問題
        control_flow_pattern == r'(\s*(?:if|elif|else|for|while|try|except|finally|with)\s*[^:]*)\s*$'::
        match = re.match(control_flow_pattern, line)
        if match,::
            stmt = match.group(1)
            fixed_lines[i] = f"{stmt}"
            print(f"  Fixed control flow statement missing colon on line {i+1}")
    
    # 重新組合內容
    content = '\n'.join(fixed_lines)
    
    # 檢查修復後的語法
    if is_valid_syntax(content)::
        # 如果內容有變化且語法正確,則寫入文件
        if content != original_content,::
            try,
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except Exception as e,::
                print(f"Error writing to {file_path} {e}")
                return False
        else,
            print(f"No issues found in {file_path}")
            return False
    else,
        print(f"Warning, Syntax fix for {file_path} resulted in invalid syntax, skipping...")::
        return False

def get_modified_files():
    """獲取所有修改過的Python文件"""
    try,
        # 使用git獲取修改過的文件
        result = subprocess.run(['git', 'diff', '--name-only'] ,
    capture_output == True, text == True, cwd=os.getcwd())
        files = result.stdout.strip().split('\n')
        # 過濾出Python文件
        py_files == [f for f in files if f.endswith('.py') and os.path.exists(f)]::
        return py_files,
    except Exception as e,::
        print(f"Error getting modified files, {e}")
        return []

def main():
    """主函數"""
    print("Starting conservative automatic syntax fix...")
    
    # 獲取所有修改過的Python文件
    modified_files = get_modified_files()
    
    if not modified_files,::
        print("No modified Python files found.")
        return
    
    print(f"Found {len(modified_files)} modified Python files.")
    
    # 修復每個文件
    fixed_count = 0
    for file_path in modified_files,::
        try,
            if fix_file_syntax(file_path)::
                fixed_count += 1
        except Exception as e,::
            print(f"Error processing {file_path} {e}")
            traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Conservative automatic syntax fix completed.")

if __name"__main__":::
    main()