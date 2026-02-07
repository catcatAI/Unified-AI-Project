#!/usr/bin/env python3
"""
批量修復錯誤的絕對導入路徑
將 'from apps.backend.src' 改為相對導入
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """修復單個文件中的導入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替換模式：from apps.backend.src.xxx.yyy import zzz
        # 需要計算相對路徑
        
        # 簡單策略：將 apps.backend.src 替換為 src
        content = content.replace('from apps.backend.src.', 'from src.')
        content = content.replace('import apps.backend.src.', 'import src.')
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    backend_src = Path(r"D:\Projects\Unified-AI-Project\apps\backend\src")
    
    if not backend_src.exists():
        print(f"❌ Backend src directory not found: {backend_src}")
        return
    
    print("🔍 Scanning for files with incorrect imports...")
    
    # 找到所有 Python 文件
    py_files = list(backend_src.rglob("*.py"))
    
    fixed_count = 0
    total_count = 0
    
    for py_file in py_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1
            print(f"✅ Fixed: {py_file.relative_to(backend_src)}")
        total_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total files scanned: {total_count}")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Files unchanged: {total_count - fixed_count}")

if __name__ == "__main__":
    main()
