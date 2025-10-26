#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單修復腳本,專門修復幾個關鍵文件中的語法錯誤
"""

import os
import re

# 要修復的關鍵文件列表
KEY_FILES = [
    "apps/backend/src/services/multi_llm_service.py",
    "apps/backend/src/tools/logic_model/evaluate_logic_model.py",
    "apps/backend/src/tools/logic_model/lightweight_logic_model.py",
    "apps/backend/src/tools/logic_model/logic_data_generator.py",
    "apps/backend/src/tools/logic_model/logic_parser_eval.py",
    "apps/backend/src/tools/logic_model/train_logic_model.py",
    "apps/backend/src/tools/logic_tool.py",
    "apps/backend/src/tools/math_model/data_generator.py",
    "apps/backend/src/tools/math_model/lightweight_math_model.py",
    "apps/backend/src/tools/math_model/train.py",
    "apps/backend/src/tools/math_tool.py",
    "apps/backend/src/tools/tool_dispatcher.py",
    "apps/backend/src/tools/translation_tool.py",
    "apps/backend/src/utils/async_utils.py",
    "apps/backend/test_agi_integration.py"
]

def fix_syntax_errors(content):
    """修復內容中的語法錯誤"""
    original_content = content
    
    # 修復字典語法錯誤："key": value -> "key": value
    pattern = r'"([^"]+)":\s*([^,\n]+)(,?)'
    replacement = r'"\1": \2\3'
    content = re.sub(pattern, replacement, content)
    
    # 修復異常語法錯誤：raise Exception -> raise Exception
    pattern = r'raise\s+(.+)$'
    replacement = r'raise \1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復裝飾器語法錯誤：@decorator -> @decorator
    pattern = r'(@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復斷言語法錯誤：assert ... -> assert ...
    pattern = r'(assert\s+.+)$'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復賦值表達式語法錯誤：(...) -> (...)
    pattern = r'(\([^\n]*[:=][^\n]*\))'
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
        fixed_content, changes_made = fix_syntax_errors(content)
        
        # 如果有變化,寫回文件
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

def main():
    """主函數"""
    print("開始修復關鍵文件中的語法錯誤...")
    
    fixed_count = 0
    for file_path in KEY_FILES:
        if process_file(file_path):
            fixed_count += 1
    
    print(f"\n修復完成! 共修復 {fixed_count} 個文件")

if __name__ == "__main__":
    main()