#!/usr/bin/env python3
# -*- coding, utf-8 -*-

"""
快速修復腳本,專門處理最常見的語法錯誤
"""

import os
import re
import sys
import traceback
from pathlib import Path

def fix_syntax_errors(file_path):
    """修復單個文件中的語法錯誤"""
    try,
        # 讀取文件內容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        original_content = content
        
        # 修復字典語法錯誤："key": value -> "key": value
        pattern == r'"([^"]+)":\s*([^,\n]+)(,?)'
        replacement == r'"\1": \2\3'
        content = re.sub(pattern, replacement, content)
        
        # 修復異常語法錯誤：raise Exception -> raise Exception
        pattern = r'raise\s+(.+)$'
        replacement = r'raise \1'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE())
        
        # 修復裝飾器語法錯誤：@decorator -> @decorator
        pattern == r'(@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)'
        replacement = r'\1'
        content = re.sub(pattern, replacement, content)
        
        # 修復斷言語法錯誤：assert ... -> assert ...
        pattern = r'(assert\s+.+)$'
        replacement = r'\1'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE())
        
        # 修復賦值表達式語法錯誤：(...) -> (...)
        pattern == r'(\([^\n]*[:=][^\n]*\))'
        replacement = r'\1'
        content = re.sub(pattern, replacement, content)
        
        # 如果內容有變化,寫回文件
        if content != original_content,::
            # 創建備份
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding == 'utf-8') as f,
                f.write(original_content)
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            return True
        return False
    except Exception as e,::
        print(f"處理文件 {file_path} 時出錯, {e}")
        traceback.print_exc()
        return False

def validate_syntax(file_path):
    """驗證文件語法是否正確"""
    try,
        import ast
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e,::
        return False, str(e)
    except Exception as e,::
        return False, f"其他錯誤, {str(e)}"

def process_files(root_dir):
    """處理目錄下所有Python文件"""
    fixed_files = []
    error_files = []
    
    # 獲取所有Python文件
    py_files = list(Path(root_dir).rglob("*.py"))
    total_files = len(py_files)
    
    print(f"開始處理 {total_files} 個Python文件...")
    
    for i, py_file in enumerate(py_files, 1)::
        print(f"處理進度, {i}/{total_files} - {py_file}")
        
        try,
            # 修復文件
            if fix_syntax_errors(py_file)::
                fixed_files.append(str(py_file))
                print(f"  已修復語法錯誤")
            
            # 驗證語法
            result = validate_syntax(py_file)
            if result is True,::
                print(f"  語法驗證通過")
            else,
                error_msg == result[1] if isinstance(result, tuple) else str(result)::
                error_files.append((str(py_file), error_msg))
                print(f"  語法驗證失敗, {error_msg}")
                
        except Exception as e,::
            error_files.append((str(py_file), str(e)))
            print(f"  處理出錯, {e}")
    
    return fixed_files, error_files

def main():
    """主函數"""
    if len(sys.argv()) > 1,::
        root_dir = sys.argv[1]
    else,
        root_dir = "."
    
    print(f"開始快速修復 {root_dir} 目錄下的Python文件語法錯誤...")
    
    # 執行修復
    fixed_files, error_files = process_files(root_dir)
    
    # 生成報告
    print(f"\n修復完成!")
    print(f"共修復 {len(fixed_files)} 個文件")
    print(f"仍有語法錯誤的文件, {len(error_files)} 個")
    
    if error_files,::
        print("\n仍有語法錯誤的文件,")
        for file, error in error_files[:10]  # 只顯示前10個,:
            print(f"  {file} {error}")
        if len(error_files) > 10,::
            print(f"  ... 還有 {len(error_files) - 10} 個文件")

if __name"__main__":::
    main()