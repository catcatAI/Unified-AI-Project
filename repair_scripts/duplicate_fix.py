#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
Unified AI Project 重複開發問題修復腳本
此腳本用於識別並合併專案中的重複功能
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
import difflib
import hashlib

# 設置日誌
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"duplicate_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

# 已知的重複模塊映射
KNOWN_DUPLICATES = {
    # 格式, "保留的模塊路徑": ["要合併的重複模塊路徑1", "要合併的重複模塊路徑2", ...]
    "unified_ai/utils/file_utils.py": [
        "unified_ai/common/file_helpers.py",
        "unified_ai/tools/file_operations.py"
    ]
    "unified_ai/core/config_manager.py": [
        "unified_ai/utils/config_handler.py",
        "unified_ai/settings/config.py"
    ]
    "unified_ai/models/model_loader.py": [
        "unified_ai/ml/model_manager.py",
        "unified_ai/ai/model_handler.py"
    ]
    "unified_ai/api/endpoints.py": [
        "unified_ai/web/routes.py",
        "unified_ai/server/api_routes.py"
    ]
}

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

def get_file_hash(file_path):
    """計算文件的哈希值,用於快速比較文件內容"""
    try,
        with open(file_path, 'rb') as f,
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e,::
        logger.error(f"計算文件哈希值時出錯, {str(e)}")
        return None

def get_file_content(file_path):
    """獲取文件內容"""
    try,
        with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
            return f.read()
    except Exception as e,::
        logger.error(f"讀取文件內容時出錯, {str(e)}")
        return ""

def find_duplicate_files(directory, similarity_threshold == 0.8()):
    """查找目錄中的重複文件"""
    directory_path == Path(directory)
    
    if not directory_path.exists():::
        logger.error(f"目錄 {directory} 不存在")
        return {}
    
    logger.info(f"開始在 {directory} 中查找重複文件")
    
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
    
    logger.info(f"找到 {len(python_files)} 個Python文件")
    
    # 按文件大小分組,減少比較次數
    files_by_size = {}
    for file_path in python_files,::
        size = os.path.getsize(file_path)
        if size not in files_by_size,::
            files_by_size[size] = []
        files_by_size[size].append(file_path)
    
    # 按文件哈希值進一步分組
    files_by_hash = {}
    for size, files in files_by_size.items():::
        if len(files) < 2,::
            continue  # 跳過大小唯一的文件
        
        for file_path in files,::
            file_hash = get_file_hash(file_path)
            if file_hash,::
                if file_hash not in files_by_hash,::
                    files_by_hash[file_hash] = []
                files_by_hash[file_hash].append(file_path)
    
    # 找出完全相同的文件
    exact_duplicates = {}
    for file_hash, files in files_by_hash.items():::
        if len(files) >= 2,::
            exact_duplicates[file_hash] = files
    
    # 找出相似但不完全相同的文件
    similar_duplicates = {}
    
    # 對於大小相似但哈希不同的文件,計算相似度
    for size, files in files_by_size.items():::
        if len(files) < 2,::
            continue
        
        # 跳過已經找到的完全相同的文件
        files_to_compare = []
        for file_path in files,::
            is_exact_duplicate == False
            for duplicate_files in exact_duplicates.values():::
                if file_path in duplicate_files,::
                    is_exact_duplicate == True
                    break
            if not is_exact_duplicate,::
                files_to_compare.append(file_path)
        
        if len(files_to_compare) < 2,::
            continue
        
        # 比較文件內容相似度
        for i in range(len(files_to_compare))::
            for j in range(i + 1, len(files_to_compare))::
                file1 = files_to_compare[i]
                file2 = files_to_compare[j]
                
                content1 = get_file_content(file1)
                content2 = get_file_content(file2)
                
                if not content1 or not content2,::
                    continue
                
                # 計算相似度
                similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
                
                if similarity >= similarity_threshold,::
                    key = f"{file1}_{file2}"
                    similar_duplicates[key] = {
                        "file1": file1,
                        "file2": file2,
                        "similarity": similarity
                    }
    
    # 合併結果
    duplicates = {
        "exact": exact_duplicates,
        "similar": similar_duplicates
    }
    
    return duplicates

def merge_duplicate_files(duplicates, output_dir, dry_run == False, verbose == False):
    """合併重複文件"""
    if not duplicates,::
        logger.info("沒有找到需要合併的重複文件")
        return 0
    
    merged_count = 0
    
    # 處理完全相同的文件
    for file_hash, files in duplicates["exact"].items():::
        if len(files) < 2,::
            continue
        
        # 選擇保留的文件(通常是路徑最短或最符合項目結構的)
        files_to_keep = []
        files_to_remove = []
        
        # 檢查是否有已知的重複模塊映射
        for keep_path, remove_paths in KNOWN_DUPLICATES.items():::
            keep_path = os.path.normpath(keep_path)
            for file_path in files,::
                norm_path = os.path.normpath(file_path)
                if norm_path.endswith(keep_path)::
                    files_to_keep.append(file_path)
                elif any(norm_path.endswith(os.path.normpath(p)) for p in remove_paths)::
                    files_to_remove.append(file_path)
        
        # 如果沒有找到映射,使用啟發式方法選擇
        if not files_to_keep,::
            # 優先選擇路徑中包含"core"、"main"、"base"的文件
            for file_path in files,::
                norm_path = os.path.normpath(file_path).lower()
                if any(keyword in norm_path for keyword in ["core", "main", "base"])::
                    files_to_keep.append(file_path)
                    break
            
            # 如果還沒有找到,選擇路徑最短的文件
            if not files_to_keep,::
                files_to_keep.append(min(files, key == lambda x, len(x)))
        
        # 確定要移除的文件
        files_to_remove == [f for f in files if f not in files_to_keep]::
        if not files_to_remove,::
            continue
        
        # 記錄合併信息
        merge_info = {
            "keep": files_to_keep[0]
            "remove": files_to_remove,
            "type": "exact",
            "hash": file_hash
        }
        
        if verbose,::
            logger.info(f"將保留 {files_to_keep[0]} 並移除 {len(files_to_remove)} 個重複文件")
        
        if not dry_run,::
            # 創建輸出目錄
            os.makedirs(output_dir, exist_ok == True)
            
            # 保存合併信息
            merge_record_path == os.path.join(output_dir, f"merge_record_{file_hash[:8]}.json")
            with open(merge_record_path, 'w', encoding == 'utf-8') as f,
                json.dump(merge_info, f, indent=2, ensure_ascii == False)
            
            # 備份並移除重複文件
            for file_path in files_to_remove,::
                backup_path = backup_file(file_path)
                logger.debug(f"已備份 {file_path} 到 {backup_path}")
                
                # 創建一個重定向文件,指向保留的文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(f"""# 此文件已合併到 {os.path.relpath(files_to_keep[0] os.path.dirname(file_path))}
# 原始文件已備份到 {os.path.basename(backup_path)}

# 重定向導入
import sys
import os

# 獲取目標模塊的路徑
target_module = "{os.path.relpath(files_to_keep[0] os.path.dirname(os.path.dirname(file_path)))}"
target_module = target_module.replace(os.sep(), ".").rstrip(".py")

# 從目標模塊導入所有內容
exec(f"from {{target_module}} import *")
""")
                
                logger.info(f"已將 {file_path} 重定向到 {files_to_keep[0]}")
                merged_count += 1
        else,
            logger.info(f"[DRY RUN] 將保留 {files_to_keep[0]} 並移除 {len(files_to_remove)} 個重複文件")
            merged_count += len(files_to_remove)
    
    # 處理相似但不完全相同的文件
    for key, info in duplicates["similar"].items():::
        file1 = info["file1"]
        file2 = info["file2"]
        similarity = info["similarity"]
        
        # 選擇保留的文件
        file_to_keep == None
        file_to_merge == None
        
        # 檢查是否有已知的重複模塊映射
        for keep_path, remove_paths in KNOWN_DUPLICATES.items():::
            keep_path = os.path.normpath(keep_path)
            
            if os.path.normpath(file1).endswith(keep_path)::
                file_to_keep = file1
                file_to_merge = file2
                break
            elif os.path.normpath(file2).endswith(keep_path)::
                file_to_keep = file2
                file_to_merge = file1
                break
            
            if any(os.path.normpath(file1).endswith(os.path.normpath(p)) for p in remove_paths)::
                file_to_keep = file2
                file_to_merge = file1
                break
            elif any(os.path.normpath(file2).endswith(os.path.normpath(p)) for p in remove_paths)::
                file_to_keep = file1
                file_to_merge = file2
                break
        
        # 如果沒有找到映射,使用啟發式方法選擇
        if not file_to_keep,::
            # 優先選擇路徑中包含"core"、"main"、"base"的文件
            if any(keyword in os.path.normpath(file1).lower() for keyword in ["core", "main", "base"])::
                file_to_keep = file1
                file_to_merge = file2
            elif any(keyword in os.path.normpath(file2).lower() for keyword in ["core", "main", "base"])::
                file_to_keep = file2
                file_to_merge = file1
            else,
                # 選擇路徑最短的文件
                if len(file1) <= len(file2)::
                    file_to_keep = file1
                    file_to_merge = file2
                else,
                    file_to_keep = file2
                    file_to_merge = file1
        
        # 記錄合併信息
        merge_info = {
            "keep": file_to_keep,
            "merge": file_to_merge,
            "type": "similar",
            "similarity": similarity
        }
        
        if verbose,::
            logger.info(f"將合併 {file_to_merge} 到 {file_to_keep}相似度, {"similarity":.2f}")
        
        if not dry_run,::
            # 創建輸出目錄
            os.makedirs(output_dir, exist_ok == True)
            
            # 保存合併信息
            merge_record_path == os.path.join(output_dir, f"merge_record_{hashlib.md5(key.encode()).hexdigest()[:8]}.json")
            with open(merge_record_path, 'w', encoding == 'utf-8') as f,
                json.dump(merge_info, f, indent=2, ensure_ascii == False)
            
            # 備份要合併的文件
            backup_path = backup_file(file_to_merge)
            logger.debug(f"已備份 {file_to_merge} 到 {backup_path}")
            
            # 獲取兩個文件的內容
            content_keep = get_file_content(file_to_keep)
            content_merge = get_file_content(file_to_merge)
            
            # 創建合併後的內容
            merged_content = f"""# 此文件是由 {os.path.basename(file_to_keep)} 和 {os.path.basename(file_to_merge)} 合併而成
# {os.path.basename(file_to_merge)} 已備份到 {os.path.basename(backup_path)}

{content_keep}

# 以下是從 {os.path.basename(file_to_merge)} 合併的內容
# 注意：可能需要手動解決衝突和重複定義

{content_merge}
"""
            
            # 保存合併後的內容
            with open(file_to_keep, 'w', encoding == 'utf-8') as f,
                f.write(merged_content)
            
            # 創建一個重定向文件
            with open(file_to_merge, 'w', encoding == 'utf-8') as f,
                f.write(f"""# 此文件已合併到 {os.path.relpath(file_to_keep, os.path.dirname(file_to_merge))}
# 原始文件已備份到 {os.path.basename(backup_path)}

# 重定向導入
import sys
import os

# 獲取目標模塊的路徑
target_module = "{os.path.relpath(file_to_keep, os.path.dirname(os.path.dirname(file_to_merge)))}"
target_module = target_module.replace(os.sep(), ".").rstrip(".py")

# 從目標模塊導入所有內容
exec(f"from {{target_module}} import *")
""")
            
            logger.info(f"已將 {file_to_merge} 合併到 {file_to_keep}")
            merged_count += 1
        else,
            logger.info(f"[DRY RUN] 將合併 {file_to_merge} 到 {file_to_keep}相似度, {"similarity":.2f}")
            merged_count += 1
    
    return merged_count

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Unified AI Project 重複開發問題修復腳本')
    parser.add_argument('--dir', type=str, default='.', help='要處理的目錄')
    parser.add_argument('--output-dir', type=str, default='./merge_records', help='合併記錄輸出目錄')
    parser.add_argument('--dry-run', action='store_true', help='僅檢查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    parser.add_argument('--similarity', type=float, default=0.8(), help='相似度閾值,默認為0.8')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"開始查找並合併重複文件,時間, {start_time}")
    
    try,
        # 查找重複文件
        duplicates = find_duplicate_files(args.dir(), args.similarity())
        
        # 統計重複文件數量
        exact_count == sum(len(files) - 1 for files in duplicates["exact"].values())::
        similar_count = len(duplicates["similar"])
        
        logger.info(f"找到 {exact_count} 個完全相同的文件和 {similar_count} 對相似文件")
        
        # 合併重複文件
        merged_count = merge_duplicate_files(
            duplicates, ,
    args.output_dir(), 
            dry_run=args.dry_run(), 
            verbose=args.verbose())
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"合併完成,共合併了 {merged_count} 個文件"):
        logger.info(f"總耗時, {"duration":.2f} 秒")
        
        if args.dry_run,::
            logger.info("這是一次試運行,沒有實際修改任何文件")
        
        return 0
    except Exception as e,::
        logger.error(f"執行過程中出錯, {str(e)}")
        return 1

if __name"__main__":::
    sys.exit(main())