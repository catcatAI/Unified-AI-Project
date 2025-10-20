#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unified AI Project 語法修復腳本
此腳本用於自動修復專案中的常見語法錯誤和問題
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"syntax_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定義常見語法錯誤的修復規則
SYNTAX_FIXES = [
    # 修復錯誤的異常語法: except Exception, e -> except Exception as e
    (r'except\s+(\w+)\s*,\s*(\w+)', r'except \1 as \2'),
    
    # 修復錯誤的raise語法: raise Exception, "message" -> raise Exception("message")
    (r'raise\s+(\w+)\s*,\s*(["\'].*?["\'])', r'raise \1(\2)'),
    
    # 修復錯誤的字典語法: dict([(key, value)]) -> {key: value}
    (r'dict\(\[(.*?)\]\)', lambda m: _fix_dict_syntax(m.group(1))),
    
    # 修復錯誤的裝飾器語法: @decorator (換行) def -> @decorator\ndef
    (r'@(\w+)\s+def', r'@\1\ndef'),
    
    # 修復錯誤的導入語法: from module import * -> from module import (具體項目)
    (r'from\s+(\w+)\s+import\s+\*', lambda m: _fix_wildcard_import(m.group(1))),
    
    # 修復錯誤的字符串格式化: "%s" % var -> f"{var}"
    (r'["\']%s["\']\s*%\s*(\w+)', r'f"{\1}"'),
    
    # 修復缺少的self參數
    (r'def\s+(\w+)\(\s*\):', lambda m: _fix_missing_self(m.group(0), m.group(1))),
    
    # 修復錯誤的路徑連接: os.path.join(path1 + "/" + path2) -> os.path.join(path1, path2)
    (r'os\.path\.join\((.*?)\s*\+\s*["\']\/["\']\s*\+\s*(.*?)\)', r'os.path.join(\1, \2)'),
    
    # 修復錯誤的相對導入: from . import module -> from package import module
    (r'from\s+\.\s+import\s+(\w+)', lambda m: _fix_relative_import(m.group(1))),
]

# 導入路徑修復規則
IMPORT_FIXES = [
    # 修復絕對導入路徑
    (r'from\s+unified_ai_project\s+import', r'from unified_ai import'),
    (r'import\s+unified_ai_project\.', r'import unified_ai.'),
    
    # 修復其他常見導入路徑問題
    (r'from\s+\.\.(\w+)\s+import', r'from unified_ai.\1 import'),
]

# 需要排除的目錄和文件
EXCLUDE_DIRS = [
    '.git', 
    'venv', 
    'env', 
    '__pycache__', 
    'node_modules', 
    'archived_docs',
    'models',
    'data'
]
EXCLUDE_FILES = [
    '.pyc', 
    '.pyo', 
    '.pyd', 
    '.so', 
    '.dll', 
    '.exe',
    '.jpg',
    '.png',
    '.mp4',
    '.zip',
    '.tar.gz'
]

def _fix_dict_syntax(dict_content):
    """修復錯誤的字典語法"""
    # 將 dict([(key, value)]) 轉換為 {key: value}
    items = []
    for item in re.findall(r'\(([^,]+),\s*([^)]+)\)', dict_content):
        key, value = item
        items.append(f"{key}: {value}")
    return "{" + ", ".join(items) + "}"

def _fix_wildcard_import(module_name):
    """修復通配符導入"""
    # 這裡需要根據實際模塊內容來確定具體導入項
    # 作為一個簡單的修復，我們可以使用一些常見的模塊導入項
    common_imports = {
        "os": "path, environ, makedirs",
        "sys": "argv, exit, path",
        "json": "loads, dumps",
        "datetime": "datetime, timedelta",
        "re": "match, search, findall, sub",
        "numpy": "array, zeros, ones",
        "torch": "nn, optim, cuda",
        "tensorflow": "keras, layers",
    }
    
    if module_name in common_imports:
        return f"from {module_name} import {common_imports[module_name]}"
    return f"from {module_name} import "  # 需要手動補充

def _fix_missing_self(method_def, method_name):
    """修復缺少的self參數"""
    # 檢查是否是類方法（需要上下文分析）
    # 這裡簡單地假設所有沒有參數的方法都需要self
    if method_name not in ["__init__", "__str__", "__repr__", "get", "set", "update", "process", "run", "execute"]:
        return method_def  # 不是常見的需要self的方法名
    return method_def.replace("():", "(self):")

def _fix_relative_import(module_name):
    """修復相對導入"""
    # 需要根據文件路徑確定正確的包名
    # 這裡使用一個簡單的假設
    return f"from unified_ai import {module_name}"

def should_exclude(path):
    """檢查是否應該排除該路徑"""
    path_str = str(path)
    
    # 檢查排除目錄
    for exclude_dir in EXCLUDE_DIRS:
        if f"/{exclude_dir}/" in path_str.replace("\\", "/") or path_str.endswith(f"/{exclude_dir}"):
            return True
    
    # 檢查排除文件
    for exclude_ext in EXCLUDE_FILES:
        if path_str.endswith(exclude_ext):
            return True
    
    return False

def backup_file(file_path):
    """備份文件"""
    backup_path = str(file_path) + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_file(file_path, dry_run=False, verbose=False):
    """修復單個文件中的語法錯誤"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # 應用語法修復規則
        for pattern, replacement in SYNTAX_FIXES:
            if callable(replacement):
                # 對於需要複雜處理的規則，使用回調函數
                matches = list(re.finditer(pattern, content))
                for match in reversed(matches):  # 從後向前替換，避免位置偏移
                    start, end = match.span()
                    fixed_text = replacement(match)
                    if fixed_text:
                        content = content[:start] + fixed_text + content[end:]
                        fixes_applied += 1
            else:
                # 對於簡單的替換規則，直接使用re.sub
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    fixes_applied += count
        
        # 應用導入路徑修復規則
        for pattern, replacement in IMPORT_FIXES:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                fixes_applied += count
        
        # 如果有修改，保存文件
        if content != original_content:
            if verbose:
                logger.info(f"修復了 {file_path} 中的 {fixes_applied} 個問題")
            
            if not dry_run:
                # 備份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已備份 {file_path} 到 {backup_path}")
                
                # 寫入修復後的內容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已修復並保存 {file_path}")
            else:
                logger.info(f"[DRY RUN] 將修復 {file_path} 中的 {fixes_applied} 個問題")
            
            return fixes_applied
        elif verbose:
            logger.debug(f"沒有在 {file_path} 中發現需要修復的問題")
        
        return 0
    except Exception as e:
        logger.error(f"處理 {file_path} 時出錯: {str(e)}")
        return 0

def fix_directory(directory, dry_run=False, verbose=False, recursive=True):
    """修復目錄中的所有Python文件"""
    directory_path = Path(directory)
    total_fixes = 0
    files_processed = 0
    
    if not directory_path.exists():
        logger.error(f"目錄 {directory} 不存在")
        return 0, 0
    
    logger.info(f"開始處理目錄: {directory}")
    
    # 獲取所有Python文件
    python_files = []
    if recursive:
        for root, dirs, files in os.walk(directory):
            # 過濾掉需要排除的目錄
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if not should_exclude(file_path):
                        python_files.append(file_path)
    else:
        for file in os.listdir(directory):
            if file.endswith('.py'):
                file_path = os.path.join(directory, file)
                if not should_exclude(file_path):
                    python_files.append(file_path)
    
    # 處理每個Python文件
    for file_path in python_files:
        files_processed += 1
        fixes = fix_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期報告進度
        if files_processed % 50 == 0:
            logger.info(f"已處理 {files_processed}/{len(python_files)} 個文件，修復了 {total_fixes} 個問題")
    
    logger.info(f"目錄 {directory} 處理完成，共處理了 {files_processed} 個文件，修復了 {total_fixes} 個問題")
    return files_processed, total_fixes

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Unified AI Project 語法修復腳本')
    parser.add_argument('--dir', type=str, default='.', help='要處理的目錄')
    parser.add_argument('--dry-run', action='store_true', help='僅檢查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    parser.add_argument('--no-recursive', action='store_true', help='不遞歸處理子目錄')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"開始修復，時間: {start_time}")
    
    try:
        files_processed, total_fixes = fix_directory(
            args.dir, 
            dry_run=args.dry_run, 
            verbose=args.verbose,
            recursive=not args.no_recursive
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修復完成，共處理了 {files_processed} 個文件，修復了 {total_fixes} 個問題")
        logger.info(f"總耗時: {duration:.2f} 秒")
        
        if args.dry_run:
            logger.info("這是一次試運行，沒有實際修改任何文件")
        
        return 0
    except Exception as e:
        logger.error(f"執行過程中出錯: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())