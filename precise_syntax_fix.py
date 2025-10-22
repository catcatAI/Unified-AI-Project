#!/usr/bin/env python3
"""
精确语法错误修复脚本
修复项目中特定的语法错误模式
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"precise_syntax_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 需要排除的目录和文件
EXCLUDE_DIRS = [
    '.git', 
    'venv', 
    'env', 
    '__pycache__', 
    'node_modules', 
    'archived_docs',
    'models',
    'data',
    'backup',
    '.pytest_cache'
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
    """检查是否应该排除该路径"""
    path_str = str(path)
    
    # 检查排除目录
    for exclude_dir in EXCLUDE_DIRS:
        if f"/{exclude_dir}/" in path_str.replace("\\", "/") or path_str.endswith(f"/{exclude_dir}"):
            return True
    
    # 检查排除文件
    for exclude_ext in EXCLUDE_FILES:
        if path_str.endswith(exclude_ext):
            return True
    
    return False

def backup_file(file_path):
    """备份文件"""
    backup_path = str(file_path) + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_specific_syntax_errors(content):
    """修复特定的语法错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复1: 修复孤立的冒号错误
    # 匹配行首或行尾的孤立冒号
    pattern = r'^\s*:\s*$'
    replacement = ''
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个孤立冒号错误")
    
    # 修复2: 修复装饰器后多余的冒号
    pattern = r'^(\s*@[\w\.]+.*)\s*:\s*$'
    replacement = r'\1'
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个装饰器后多余的冒号")
    
    # 修复3: 修复字典字面量语法错误
    # 修复 "key": value 的错误
    pattern = r'_\s*=\s*"([^"]+)"\s*:\s*([^,\n}\]]*)'
    replacement = r'"\1": \2'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个字典字面量语法错误")
    
    # 修复4: 修复单引号字典字面量语法错误
    pattern = r"_\s*=\s*'([^']+)'\s*:\s*([^,\n}\]]*)"
    replacement = r"'\1': \2"
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个单引号字典字面量语法错误")
    
    # 修复5: 修复无效的赋值语法
    pattern = r'_\s*=\s*raise\s+'
    replacement = 'raise '
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的 raise 赋值语法")
    
    pattern = r'_\s*=\s*assert\s+'
    replacement = 'assert '
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的 assert 赋值语法")
    
    # 修复6: 修复不完整的导入语句
    pattern = r'from\s+[\w\.]+\s+import\s*$'
    replacement = ''
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个不完整的导入语句")
    
    # 修复7: 修复多余的逗号错误
    pattern = r',\s*\)'
    replacement = ')'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个多余的逗号错误")
    
    # 修复8: 修复无效的关键字参数语法
    pattern = r'(\w+)\s*=\s*=+\s*(\w+)'
    replacement = r'\1=\2'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的关键字参数语法")
    
    return content, fixes_applied

def fix_syntax_errors_in_file(file_path, dry_run=False, verbose=False):
    """修复单个文件中的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        
        # 应用特定的语法修复
        content, fixes_applied = fix_specific_syntax_errors(content)
        
        # 如果有修改,保存文件
        if content != original_content:
            if verbose:
                logger.info(f"修复了 {file_path} 中的 {fixes_applied} 个语法错误")
            
            if not dry_run:
                # 备份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已备份 {file_path} 到 {backup_path}")
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已修复并保存 {file_path}")
            else:
                logger.info(f"[DRY RUN] 将修复 {file_path} 中的 {fixes_applied} 个语法错误")
            
            return fixes_applied
        elif verbose:
            logger.debug(f"没有在 {file_path} 中发现需要修复的语法错误")
        
        return 0
    except Exception as e:
        logger.error(f"处理 {file_path} 时出错: {str(e)}")
        return 0

def fix_directory(directory, dry_run=False, verbose=False):
    """修复目录中的所有Python文件"""
    directory_path = Path(directory)
    total_fixes = 0
    files_processed = 0
    
    if not directory_path.exists():
        logger.error(f"目录 {directory} 不存在")
        return 0, 0
    
    logger.info(f"开始处理目录: {directory}")
    
    # 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 过滤掉需要排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not should_exclude(file_path):
                    python_files.append(file_path)
    
    # 处理每个Python文件
    for file_path in python_files:
        files_processed += 1
        fixes = fix_syntax_errors_in_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期报告进度
        if files_processed % 50 == 0:
            logger.info(f"已处理 {files_processed}/{len(python_files)} 个文件,修复了 {total_fixes} 个语法错误")
    
    logger.info(f"目录 {directory} 处理完成,共处理了 {files_processed} 个文件,修复了 {total_fixes} 个错误")
    return files_processed, total_fixes

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='精确语法错误修复脚本')
    parser.add_argument('--dir', type=str, default='.', help='要处理的目录')
    parser.add_argument('--dry-run', action='store_true', help='仅检查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"开始修复,时间: {start_time}")
    
    try:
        files_processed, total_fixes = fix_directory(
            args.dir, 
            dry_run=args.dry_run, 
            verbose=args.verbose)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修复完成,共处理了 {files_processed} 个文件,修复了 {total_fixes} 个错误")
        logger.info(f"总耗时: {duration:.2f} 秒")
        
        if args.dry_run:
            logger.info("这是一次试运行,没有实际修改任何文件")
        
        return 0
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())