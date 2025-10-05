#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
關鍵文件修復腳本，專門修復幾個最重要的文件
"""

import os
import re

# 要修復的關鍵文件列表
KEY_FILES = [
    "apps/backend/src/optimization/performance_optimizer.py",
    "apps/backend/src/security/audit_logger.py",
    "apps/backend/src/security/enhanced_sandbox.py",
    "apps/backend/src/services/ai_editor.py",
    "apps/backend/src/services/atlassian_api.py",
    "apps/backend/src/services/audio_service.py",
    "apps/backend/src/services/main_api_server.py",
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
    "apps/backend/src/utils/async_utils.py",
    "apps/backend/test_agi_integration.py"
]

def fix_assignment_syntax(content):
    """修復帶有 '_ = ' 前綴的語法錯誤"""
    original_content = content
    
    # 修復字典語法錯誤：_ = "key": value -> "key": value
    pattern = r'_ = "([^"]+)":\s*([^,\n]+)(,?)'
    replacement = r'"\1": \2\3'
    content = re.sub(pattern, replacement, content)
    
    # 修復異常語法錯誤：_ = raise Exception -> raise Exception
    pattern = r'_ = raise\s+(.+)$'
    replacement = r'raise \1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 修復裝飾器語法錯誤：_ = @decorator -> @decorator
    pattern = r'_ = (@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)'
    replacement = r'\1'
    content = re.sub(pattern, replacement, content)
    
    # 修復斷言語法錯誤：_ = assert ... -> assert ...
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
    
    # 修復展開字典語法錯誤：_ = **dict -> **dict
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
        return True
    except:
        return False

def main():
    """主函數"""
    print("開始修復關鍵文件...")
    
    fixed_count = 0
    valid_count = 0
    
    for file_path in KEY_FILES:
        # 修復文件
        if process_file(file_path):
            fixed_count += 1
        
        # 驗證語法
        if validate_syntax(file_path):
            valid_count += 1
            print(f"  語法正確: {file_path}")
        else:
            print(f"  語法錯誤: {file_path}")
    
    print(f"\n修復完成!")
    print(f"共修復 {fixed_count} 個文件")
    print(f"語法正確 {valid_count} 個文件")

if __name__ == "__main__":
    main()