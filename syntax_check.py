#!/usr/bin/env python3
"""
真實系統語法檢查器
基於真實Python編譯器驗證語法
"""

import ast
import os
import sys
from pathlib import Path

def check_file_syntax(filepath):
    """檢查單個文件的語法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 使用真實Python AST編譯器
        ast.parse(source, filename=filepath)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg} - {e.text.strip() if e.text else 'N/A'}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def main():
    # 檢查訓練系統文件
    training_files = [
        'training/train_model.py',
        'training/auto_training_manager.py', 
        'training/enhanced_checkpoint_manager.py'
    ]
    
    print("🔍 真實系統語法檢查 (基於真實Python編譯器)")
    print("=" * 60)
    
    all_passed = True
    for file_path in training_files:
        if os.path.exists(file_path):
            success, error = check_file_syntax(file_path)
            if success:
                print(f"✅ {file_path}: 語法正確")
            else:
                print(f"❌ {file_path}: {error}")
                all_passed = False
        else:
            print(f"⚠️  {file_path}: 文件不存在")
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有文件語法檢查通過")
    else:
        print("⚠️  發現語法錯誤，需要修復")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())