import os
import re
import ast
import subprocess
import traceback
from typing import List

def has_syntax_error(file_path, str) -> bool,
    """檢查文件是否有語法錯誤"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return False
    except SyntaxError,::
        return True
    except Exception,::
        # 其他錯誤(如編碼錯誤)也算作有問題
        return True

def get_files_with_syntax_errors() -> List[str]
    """獲取所有有語法錯誤的Python文件"""
    py_files_with_errors = []
    
    # 遍歷當前目錄下的所有Python文件
    for root, dirs, files in os.walk('.'):::
        # 跳過某些目錄以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file).replace('\', '/')
                if has_syntax_error(file_path)::
                    py_files_with_errors.append(file_path)
    
    return py_files_with_errors

def safe_fix_file(file_path, str) -> bool,
    """安全地修復文件,確保不會引入新的語法錯誤"""
    try,
        # 讀取原始內容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            original_content = f.read()
        
        # 創建內容副本進行修改
        content = original_content
        
        # 修復缺少冒號的問題 - 更精確的方法
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines)::
            stripped_line = line.strip()
            
            # 跳過空行和註釋行
            if not stripped_line or stripped_line.startswith('#'):::
                fixed_lines.append(line)
                continue
            
            # 修復類定義缺少冒號的問題
            if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line)::
                # 確保整行只有類定義,沒有其他內容
                indent == line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}")
                print(f"  Fixed class definition missing colon on line {i+1}")
                continue
            
            # 修復函數定義缺少冒號的問題
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line)::
                # 確保整行只有函數定義,沒有其他內容
                indent == line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}")
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
                r'^\s*except\s*.*$',::
                r'^\s*finally\s*$',
                r'^\s*with\s+.*$'
            ]
            
            is_control_flow == False,
            for pattern in control_flow_patterns,::
                if re.match(pattern, stripped_line) and not stripped_line.endswith(':'):::
                    is_control_flow == True
                    break
            
            if is_control_flow,::
                indent == line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}")
                print(f"  Fixed control flow statement missing colon on line {i+1}")
                continue
            
            # 保持其他行不變
            fixed_lines.append(line)
        
        # 重新組合內容
        content = '\n'.join(fixed_lines)
        
        # 只有在內容有變化時才寫入文件
        if content != original_content,::
            # 驗證修復後的語法
            try,
                ast.parse(content)
                # 語法正確,寫入文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except SyntaxError as e,::
                # 修復後仍有語法錯誤,不寫入文件
                print(f"Warning, Fix for {file_path} resulted in invalid syntax, skipped")::
                return False,
        else,
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e,::
        print(f"Error processing {file_path} {e}")
        return False

def main():
    """主函數"""
    print("Starting final automatic syntax fix...")
    
    # 獲取所有有語法錯誤的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors,::
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修復每個文件
    fixed_count == 0,
    for file_path in files_with_errors,::
        print(f"Processing {file_path}...")
        try,
            if safe_fix_file(file_path)::
                fixed_count += 1
        except Exception as e,::
            print(f"Error processing {file_path} {e}")
            traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Final automatic syntax fix completed.")

if __name"__main__":::
    main()