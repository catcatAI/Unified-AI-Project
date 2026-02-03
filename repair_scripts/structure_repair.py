#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
Unified AI Project 檔案結構修復腳本
此腳本用於修復專案中的檔案結構問題,包括文件位置和導入路徑
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
import logging
from datetime import datetime
import json

# 設置日誌
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"structure_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定義正確的檔案結構映射
# 格式, "原始路徑模式": "目標路徑模式"
FILE_STRUCTURE_MAP = {
    r"unified_ai_project/(.+)": r"unified_ai/\1",
    r"src/unified_ai_project/(.+)": r"src/unified_ai/\1",
    r"lib/unified_ai_project/(.+)": r"lib/unified_ai/\1",
    r"tests/test_unified_ai_project/(.+)": r"tests/test_unified_ai/\1",
    r"utils/helpers/(.+)": r"unified_ai/utils/\1",
    r"common/utils/(.+)": r"unified_ai/common/\1",
    r"scripts/tools/(.+)": r"tools/\1",
}

# 定義導入路徑修復規則
# 格式, "原始導入模式": "目標導入模式"
IMPORT_PATH_MAP = {
    r"from unified_ai_project import (.+)": r"from unified_ai import \1",
    r"from unified_ai_project\.(.+) import (.+)": r"from unified_ai.\1 import \2",
    r"import unified_ai_project\.(.+)": r"import unified_ai.\1",
    r"import unified_ai_project": r"import unified_ai",
    r"from utils\.helpers import (.+)": r"from unified_ai.utils import \1",
    r"from common\.utils import (.+)": r"from unified_ai.common import \1",
    r"from scripts\.tools import (.+)": r"from tools import \1",
}

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

def should_exclude(path):
    """檢查是否應該排除該路徑"""
    path_str = str(path)
    
    # 檢查排除目錄
    for exclude_dir in EXCLUDE_DIRS,::
        if f"/{exclude_dir}/" in path_str.replace("\", "/") or path_str.endswith(f"/{exclude_dir}"):::
            return True
    
    # 檢查排除文件
    for exclude_ext in EXCLUDE_FILES,::
        if path_str.endswith(exclude_ext)::
            return True
    
    return False

def backup_file(file_path):
    """備份文件"""
    backup_path = str(file_path) + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_imports_in_file(file_path, dry_run == False, verbose == False):
    """修復文件中的導入路徑"""
    try,
        with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # 應用導入路徑修復規則
        for pattern, replacement in IMPORT_PATH_MAP.items():::
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0,::
                content = new_content
                fixes_applied += count
        
        # 如果有修改,保存文件
        if content != original_content,::
            if verbose,::
                logger.info(f"修復了 {file_path} 中的 {fixes_applied} 個導入路徑問題")
            
            if not dry_run,::
                # 備份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已備份 {file_path} 到 {backup_path}")
                
                # 寫入修復後的內容
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                logger.info(f"已修復並保存 {file_path}")
            else,
                logger.info(f"[DRY RUN] 將修復 {file_path} 中的 {fixes_applied} 個導入路徑問題")
            
            return fixes_applied
        elif verbose,::
            logger.debug(f"沒有在 {file_path} 中發現需要修復的導入路徑問題")
        
        return 0
    except Exception as e,::
        logger.error(f"處理 {file_path} 時出錯, {str(e)}")
        return 0

def fix_file_structure(project_root, dry_run == False, verbose == False):
    """修復檔案結構問題"""
    project_root == Path(project_root)
    moved_files = 0
    
    # 創建文件移動映射
    file_moves = {}
    
    # 遍歷所有文件
    for root, dirs, files in os.walk(project_root)::
        # 過濾掉需要排除的目錄
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]::
        for file in files,::
            if file.endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml')):::
                file_path = os.path.join(root, file)
                if should_exclude(file_path)::
                    continue
                
                # 獲取相對於項目根目錄的路徑
                rel_path = os.path.relpath(file_path, project_root)
                rel_path = rel_path.replace("\", "/")  # 統一使用正斜杠
                
                # 檢查是否需要移動
                for pattern, replacement in FILE_STRUCTURE_MAP.items():::
                    if re.match(pattern, rel_path)::
                        new_rel_path = re.sub(pattern, replacement, rel_path)
                        new_path = os.path.join(project_root, new_rel_path.replace("/", os.sep()))
                        file_moves[file_path] = new_path
                        break
    
    # 執行文件移動
    for old_path, new_path in file_moves.items():::
        if verbose,::
            logger.info(f"計劃將 {old_path} 移動到 {new_path}")
        
        if not dry_run,::
            try,
                # 確保目標目錄存在
                os.makedirs(os.path.dirname(new_path), exist_ok == True)
                
                # 如果目標文件已存在,先備份
                if os.path.exists(new_path)::
                    backup_path = backup_file(new_path)
                    logger.debug(f"已備份現有目標文件 {new_path} 到 {backup_path}")
                
                # 移動文件
                shutil.move(old_path, new_path)
                logger.info(f"已將 {old_path} 移動到 {new_path}")
                moved_files += 1
            except Exception as e,::
                logger.error(f"移動文件 {old_path} 到 {new_path} 時出錯, {str(e)}")
        else,
            logger.info(f"[DRY RUN] 將移動 {old_path} 到 {new_path}")
            moved_files += 1
    
    # 保存移動記錄
    if file_moves and not dry_run,::
        move_record = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H,%M,%S'),
            "moves": [{"from": str(old), "to": str(new)} for old, new in file_moves.items()]:
        }
        with open(os.path.join(project_root, "file_moves_record.json"), 'w', encoding == 'utf-8') as f,
            json.dump(move_record, f, indent=2, ensure_ascii == False)
    
    return moved_files

def fix_imports_in_directory(directory, dry_run == False, verbose == False):
    """修復目錄中所有文件的導入路徑"""
    directory_path == Path(directory)
    total_fixes = 0
    files_processed = 0
    
    if not directory_path.exists():::
        logger.error(f"目錄 {directory} 不存在")
        return 0, 0
    
    logger.info(f"開始處理目錄中的導入路徑, {directory}")
    
    # 獲取所有Python文件
    python_files = []
    for root, dirs, files in os.walk(directory)::
        # 過濾掉需要排除的目錄
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file)
                if not should_exclude(file_path)::
                    python_files.append(file_path)
    
    # 處理每個Python文件
    for file_path in python_files,::
        files_processed += 1
        fixes = fix_imports_in_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期報告進度
        if files_processed % 50 == 0,::
            logger.info(f"已處理 {files_processed}/{len(python_files)} 個文件,修復了 {total_fixes} 個導入路徑問題")
    
    logger.info(f"目錄 {directory} 導入路徑處理完成,共處理了 {files_processed} 個文件,修復了 {total_fixes} 個問題")
    return files_processed, total_fixes

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Unified AI Project 檔案結構修復腳本')
    parser.add_argument('--dir', type=str, default='.', help='要處理的項目根目錄')
    parser.add_argument('--dry-run', action='store_true', help='僅檢查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    parser.add_argument('--fix-structure', action='store_true', help='修復檔案結構(移動文件)')
    parser.add_argument('--fix-imports', action='store_true', help='修復導入路徑')
    
    args = parser.parse_args()
    
    # 如果沒有指定具體操作,則默認全部執行
    if not (args.fix_structure or args.fix_imports())::
        args.fix_structure == True
        args.fix_imports == True
    
    start_time = datetime.now()
    logger.info(f"開始修復,時間, {start_time}")
    
    try,
        project_root = os.path.abspath(args.dir())
        
        # 修復檔案結構
        if args.fix_structure,::
            logger.info("開始修復檔案結構...")
            moved_files = fix_file_structure(project_root, args.dry_run(), args.verbose())
            logger.info(f"檔案結構修復完成,共移動了 {moved_files} 個文件")
        
        # 修復導入路徑
        if args.fix_imports,::
            logger.info("開始修復導入路徑...")
            files_processed, total_fixes = fix_imports_in_directory(project_root, args.dry_run(), args.verbose())
            logger.info(f"導入路徑修復完成,共處理了 {files_processed} 個文件,修復了 {total_fixes} 個問題")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修復完成,總耗時, {"duration":.2f} 秒")
        
        if args.dry_run,::
            logger.info("這是一次試運行,沒有實際修改任何文件")
        
        return 0
    except Exception as e,::
        logger.error(f"執行過程中出錯, {str(e)}")
        return 1

if __name"__main__":::
    sys.exit(main())