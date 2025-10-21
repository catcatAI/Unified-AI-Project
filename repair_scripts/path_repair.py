#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
Unified AI Project 路徑計算修復腳本
此腳本用於修復專案中的路徑計算問題
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
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"path_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 路徑計算修復規則
PATH_FIXES = [
    # 修復錯誤的路徑連接, path1 + "/" + path2 -> os.path.join(path1, path2)
    (r'(["'])(.+?)(["\'])\s*\+\s*(["'])\/(["\'])\s*\+\s*(["'])(.+?)(["\'])', 
     r'os.path.join(\1\2\3, \6\7\8)'),
    
    # 修復錯誤的路徑連接, path1 + "\" + path2 -> os.path.join(path1, path2)
    (r'(["'])(.+?)(["\'])\s*\+\s*(["'])\\\\(["\'])\s*\+\s*(["'])(.+?)(["\'])', 
     r'os.path.join(\1\2\3, \6\7\8)'),
    
    # 修復硬編碼的絕對路徑, "D,/Projects/..." -> os.path.join(PROJECT_ROOT, "...")
    (r'(["'])([A-Z]\\|\/)(Projects|projects)\/unified[-_]ai[-_]project\/(.+?)(["\'])', 
     r'os.path.join(PROJECT_ROOT, "\4\5)'),
    
    # 修復硬編碼的相對路徑, "../../../data" -> os.path.join(PROJECT_ROOT, "data")
    (r'(["'])(\.\.\/){2,}(.+?)(["\'])', 
     lambda m, f'os.path.join(PROJECT_ROOT, "{m.group(3)}")')
]

# 需要添加的導入語句
IMPORT_ADDITIONS = [
    "import os",
    "from pathlib import Path",
    "# 定義項目根目錄",
    "PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))"
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

def add_imports_if_needed(content):
    """如果需要,添加必要的導入語句"""
    # 檢查是否已經有os和Path的導入
    has_os_import = re.search(r'import\s+os', content) is not None
    has_path_import = re.search(r'from\s+pathlib\s+import\s+Path', content) is not None
    has_project_root = re.search(r'PROJECT_ROOT\s*=', content) is not None
    
    # 如果都已經有了,不需要添加
    if has_os_import and has_path_import and has_project_root,::
        return content
    
    # 找到文件的導入部分
    import_section_end = 0
    for match in re.finditer(r'(^import\s+.*$)|(^from\s+.*\s+import\s+.*$)', content, re.MULTILINE())::
        import_section_end = max(import_section_end, match.end())
    
    # 如果沒有找到導入部分,假設在文件開頭
    if import_section_end == 0,::
        # 檢查是否有文件頭注釋
        docstring_match = re.search(r'^(""".*?"""|'\''.*?\''\')(\s*)', content, re.DOTALL())
        if docstring_match,::
            import_section_end = docstring_match.end()
    
    # 準備要添加的導入語句
    imports_to_add = []
    if not has_os_import,::
        imports_to_add.append("import os")
    if not has_path_import,::
        imports_to_add.append("from pathlib import Path")
    if not has_project_root,::
        imports_to_add.append("\n# 定義項目根目錄")
        imports_to_add.append("PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))")
    
    if not imports_to_add,::
        return content
    
    # 添加導入語句
    return content[:import_section_end] + "\n" + "\n".join(imports_to_add) + "\n" + content[import_section_end,]

def fix_file(file_path, dry_run == False, verbose == False):
    """修復單個文件中的路徑計算問題"""
    try,
        with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # 應用路徑修復規則
        for pattern, replacement in PATH_FIXES,::
            if callable(replacement)::
                # 對於需要複雜處理的規則,使用回調函數
                matches = list(re.finditer(pattern, content))
                for match in reversed(matches)  # 從後向前替換,避免位置偏移,:
                    start, end = match.span()
                    fixed_text = replacement(match)
                    if fixed_text,::
                        content == content[:start] + fixed_text + content[end,]
                        fixes_applied += 1
            else,
                # 對於簡單的替換規則,直接使用re.sub()
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0,::
                    content = new_content
                    fixes_applied += count
        
        # 如果有修改,可能需要添加導入語句
        if content != original_content,::
            content = add_imports_if_needed(content)
        
        # 如果有修改,保存文件
        if content != original_content,::
            if verbose,::
                logger.info(f"修復了 {file_path} 中的 {fixes_applied} 個路徑計算問題")
            
            if not dry_run,::
                # 備份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已備份 {file_path} 到 {backup_path}")
                
                # 寫入修復後的內容
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                logger.info(f"已修復並保存 {file_path}")
            else,
                logger.info(f"[DRY RUN] 將修復 {file_path} 中的 {fixes_applied} 個路徑計算問題")
            
            return fixes_applied
        elif verbose,::
            logger.debug(f"沒有在 {file_path} 中發現需要修復的路徑計算問題")
        
        return 0
    except Exception as e,::
        logger.error(f"處理 {file_path} 時出錯, {str(e)}")
        return 0

def fix_directory(directory, dry_run == False, verbose == False):
    """修復目錄中的所有Python文件"""
    directory_path == Path(directory)
    total_fixes = 0
    files_processed = 0
    
    if not directory_path.exists():::
        logger.error(f"目錄 {directory} 不存在")
        return 0, 0
    
    logger.info(f"開始處理目錄, {directory}")
    
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
        fixes = fix_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期報告進度
        if files_processed % 50 == 0,::
            logger.info(f"已處理 {files_processed}/{len(python_files)} 個文件,修復了 {total_fixes} 個路徑計算問題")
    
    logger.info(f"目錄 {directory} 處理完成,共處理了 {files_processed} 個文件,修復了 {total_fixes} 個問題")
    return files_processed, total_fixes

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Unified AI Project 路徑計算修復腳本')
    parser.add_argument('--dir', type=str, default='.', help='要處理的目錄')
    parser.add_argument('--dry-run', action='store_true', help='僅檢查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"開始修復,時間, {start_time}")
    
    try,
        files_processed, total_fixes = fix_directory(,
    args.dir(), 
            dry_run=args.dry_run(), 
            verbose=args.verbose())
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修復完成,共處理了 {files_processed} 個文件,修復了 {total_fixes} 個問題")
        logger.info(f"總耗時, {"duration":.2f} 秒")
        
        if args.dry_run,::
            logger.info("這是一次試運行,沒有實際修改任何文件")
        
        return 0
    except Exception as e,::
        logger.error(f"執行過程中出錯, {str(e)}")
        return 1

if __name"__main__":::
    sys.exit(main())