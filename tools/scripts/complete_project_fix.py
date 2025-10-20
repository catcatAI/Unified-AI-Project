#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整項目修復腳本，處理項目中所有帶有 '_ = ' 前綴的語法錯誤
"""

import os
import re
import sys
import traceback
from pathlib import Path

def fix_assignment_syntax(content):
    """修復各種帶有 '_ = ' 前綴的語法錯誤"""
    original_content = content
    
    # 修復字典語法錯誤："key": value -> "key": value
    pattern = r'_ = "([^"]+)":\s*([^,\n]+)(,?)'
    replacement = r'"\1": \2\3'
    content = re.sub(pattern, replacement, content)
    
    # 修復異常語法錯誤：raise Exception -> raise Exception
    pattern = r'_ = raise\s+(.+)$'
    replacement = r'raise \1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復裝飾器語法錯誤：@decorator -> @decorator
    pattern = r'_ = (@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復斷言語法錯誤：assert ... -> assert ...
    pattern = r'_ = (assert\s+.+)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復賦值表達式語法錯誤：_ = (...) -> (...)
    pattern = r'_ = (\([^\n]*[:=][^\n]*\))'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復函數參數語法錯誤：_ = param: type -> param: type
    pattern = r'_ = ([a-zA-Z_][a-zA-Z0-9_]*:\s*[a-zA-Z_][a-zA-Z0-9_.]*)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復變量賦值語法錯誤：_ = variable = value -> variable = value
    pattern = r'_ = ([a-zA-Z_][a-zA-Z0-9_]*\s*=)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復返回語句語法錯誤：_ = return value -> return value
    pattern = r'_ = (return\s+.+)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復導入語法錯誤：_ = import ... -> import ...
    pattern = r'_ = (import\s+.+)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復 from 導入語法錯誤：_ = from ... import ... -> from ... import ...
    pattern = r'_ = (from\s+[a-zA-Z_][a-zA-Z0-9_.]*\s+import\s+.+)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復字符串語法錯誤：_ = "string" -> "string"
    pattern = r'_ = ("[^"]*")'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復列表語法錯誤：_ = [item1, item2] -> [item1, item2]
    pattern = r'_ = (\[[^\]]*\])'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復註釋語法錯誤：_ = # comment -> # comment
    pattern = r'_ = (#.*)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復展開字典語法錯誤：**dict -> **dict
    pattern = r'_ = (\*\*[a-zA-Z_][a-zA-Z0-9_]*)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復關鍵字參數語法錯誤：_ = key=value -> key=value
    pattern = r'_ = ([a-zA-Z_][a-zA-Z0-9_]*=[^,\n)]*)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    return content, content != original_content

def process_file(file_path):
    """處理單個文件"""
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
            
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修復語法錯誤
        fixed_content, changes_made = fix_assignment_syntax(content)
        
        # 如果有變化，寫回文件
        if changes_made:
            # 創建備份
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"已修復: {file_path}")
            return True
        else:
            print(f"無需修復: {file_path}")
            return False
            
    except Exception as e:
        print(f"處理文件 {file_path} 時出錯: {e}")
        return False

def validate_syntax(file_path):
    """驗證文件語法"""
    try:
        import ast
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"語法錯誤: {str(e)}"
    except Exception as e:
        return False, f"其他錯誤: {str(e)}"

def main():
    """主函數"""
    print("開始完整修復項目中的語法錯誤...")
    
    # 獲取所有Python文件
    py_files = list(Path(".").rglob("*.py"))
    total_files = len(py_files)
    
    print(f"找到 {total_files} 個Python文件")
    
    fixed_count = 0
    error_count = 0
    
    # 處理每個文件
    for i, py_file in enumerate(py_files, 1):
        print(f"處理進度: {i}/{total_files} - {py_file}")
        
        try:
            # 修復文件
            if process_file(str(py_file)):
                fixed_count += 1
            
            # 驗證語法
            is_valid, error_msg = validate_syntax(str(py_file))
            if not is_valid:
                print(f"  語法錯誤: {py_file} - {error_msg}")
                error_count += 1
                    
        except Exception as e:
            print(f"  處理出錯: {e}")
    
    print(f"\n修復完成!")
    print(f"共修復 {fixed_count} 個文件")
    print(f"語法錯誤文件: {error_count} 個")

if __name__ == "__main__":
    main()