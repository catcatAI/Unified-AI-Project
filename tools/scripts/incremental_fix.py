#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增量修復腳本，逐步修復項目中的語法錯誤
"""

import os
import re
import sys
import json
import traceback
from pathlib import Path

# 定義要修復的語法錯誤模式
FIX_PATTERNS = [
    # 字典語法錯誤："key": value -> "key": value
    (r'_ = "([^"]+)":\s*([^,\n]+)(,?)', r'"\1": \2\3'),
    
    # 異常語法錯誤：raise Exception -> raise Exception
    (r'_ = raise\s+(.+)$', r'raise \1'),
    
    # 裝飾器語法錯誤：@decorator -> @decorator
    (r'_ = (@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)', r'\1'),
    
    # 斷言語法錯誤：assert ... -> assert ...
    (r'_ = (assert\s+.+)$', r'\1'),
    
    # 賦值表達式語法錯誤：_ = (...) -> (...)
    (r'_ = (\([^\n]*[:=][^\n]*\))', r'\1'),
]

def fix_syntax_errors(content):
    """修復內容中的語法錯誤"""
    original_content = content
    changes_made = False
    
    for pattern, replacement in FIX_PATTERNS:
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if new_content != content:
            content = new_content
            changes_made = True
    
    return content, changes_made

def process_file(file_path, fix_report):
    """處理單個文件"""
    try:
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修復語法錯誤
        fixed_content, changes_made = fix_syntax_errors(content)
        
        # 如果有變化，寫回文件
        if changes_made:
            # 創建備份
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            fix_report['fixed_files'].append(str(file_path))
            print(f"  已修復: {file_path}")
            return True
        else:
            print(f"  無需修復: {file_path}")
            return False
            
    except Exception as e:
        error_msg = f"處理文件時出錯: {str(e)}"
        fix_report['error_files'].append((str(file_path), error_msg))
        print(f"  錯誤: {file_path} - {error_msg}")
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

def process_directory(root_dir, fix_report):
    """處理目錄中的所有Python文件"""
    # 獲取所有Python文件
    py_files = []
    for py_file in Path(root_dir).rglob("*.py"):
        py_files.append(py_file)
    
    total_files = len(py_files)
    print(f"找到 {total_files} 個Python文件")
    
    # 處理每個文件
    for i, py_file in enumerate(py_files, 1):
        print(f"處理進度: {i}/{total_files} - {py_file}")
        
        # 修復文件
        process_file(py_file, fix_report)
        
        # 驗證語法（僅驗證前100個文件以節省時間）
        if i <= 100:
            is_valid, error_msg = validate_syntax(py_file)
            if not is_valid:
                fix_report['syntax_errors'].append((str(py_file), error_msg))
                print(f"  語法錯誤: {py_file} - {error_msg}")

def save_fix_report(fix_report):
    """保存修復報告"""
    try:
        with open("INCREMENTAL_FIX_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(fix_report, f, ensure_ascii=False, indent=2)
        print("\n修復報告已保存到 INCREMENTAL_FIX_REPORT.json")
    except Exception as e:
        print(f"保存修復報告時出錯: {e}")

def main():
    """主函數"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    print(f"開始增量修復 {root_dir} 目錄下的Python文件語法錯誤...")
    
    # 初始化修復報告
    fix_report = {
        'fixed_files': [],
        'error_files': [],
        'syntax_errors': []
    }
    
    try:
        # 執行修復
        process_directory(root_dir, fix_report)
        
        # 生成統計信息
        print(f"\n修復完成!")
        print(f"共修復 {len(fix_report['fixed_files'])} 個文件")
        print(f"處理錯誤 {len(fix_report['error_files'])} 個文件")
        print(f"語法錯誤 {len(fix_report['syntax_errors'])} 個文件 (前100個文件)")
        
        # 保存報告
        save_fix_report(fix_report)
        
    except KeyboardInterrupt:
        print("\n用戶中斷了修復過程")
        save_fix_report(fix_report)
    except Exception as e:
        print(f"\n修復過程中發生錯誤: {e}")
        traceback.print_exc()
        save_fix_report(fix_report)

if __name__ == "__main__":
    main()