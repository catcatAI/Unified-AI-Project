#!/usr/bin/env python3
"""
最终精确修复脚本
针对项目中剩余的特定语法错误进行精确修复
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
import logging
from datetime import datetime
import ast

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"final_precision_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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
    '.pytest_cache',
    'unified_fix_backups',
    'enhanced_unified_fix_backups'
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

def validate_syntax(content):
    """验证语法是否正确"""
    try:
        ast.parse(content)
        return True
    except:
        return False

def fix_colon_errors(content):
    """修复缺少冒号的错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复函数定义缺少冒号的问题
    pattern = r'(def\s+\w+\s*\([^)]*\))\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个函数定义缺少冒号的问题")
    
    # 修复类定义缺少冒号的问题
    pattern = r'(class\s+\w+\s*\(?[^)]*\)?)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个类定义缺少冒号的问题")
    
    # 修复if语句缺少冒号的问题
    pattern = r'(if\s+[^:]+)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个if语句缺少冒号的问题")
    
    # 修复for循环缺少冒号的问题
    pattern = r'(for\s+[^:]+)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个for循环缺少冒号的问题")
    
    # 修复while循环缺少冒号的问题
    pattern = r'(while\s+[^:]+)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个while循环缺少冒号的问题")
    
    # 修复try语句缺少冒号的问题
    pattern = r'(try)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个try语句缺少冒号的问题")
    
    # 修复except语句缺少冒号的问题
    pattern = r'(except[^:]*?)\s*\n'
    replacement = r'\1:\n'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个except语句缺少冒号的问题")
    
    return content, fixes_applied

def fix_assignment_errors(content):
    """修复赋值语法错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复无效的赋值语法 _ = "key": value
    pattern = r'_\s*=\s*("[^"]+")\s*:\s*([^,\n}\]]*)'
    replacement = r'\1: \2'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的字典赋值语法")
    
    # 修复单引号版本
    pattern = r"_\s*=\s*'([^']+)'\s*:\s*([^,\n}\]]*)"
    replacement = r"'\1': \2"
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个单引号无效的字典赋值语法")
    
    # 修复 _ = raise 错误
    pattern = r'_\s*=\s*raise\s+'
    replacement = 'raise '
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的raise赋值语法")
    
    # 修复 _ = assert 错误
    pattern = r'_\s*=\s*assert\s+'
    replacement = 'assert '
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个无效的assert赋值语法")
    
    return content, fixes_applied

def fix_import_errors(content):
    """修复导入语法错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复不完整的导入语句
    pattern = r'from\s+[\w\.]+\s+import\s*$'
    replacement = ''
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个不完整的导入语句")
    
    return content, fixes_applied

def fix_bracket_errors(content):
    """修复括号和逗号错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复多余的逗号错误
    pattern = r',\s*\)'
    replacement = ')'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个多余的逗号错误")
    
    # 修复多余的逗号在列表中
    pattern = r',\s*\]'
    replacement = ']'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个列表中多余的逗号错误")
    
    return content, fixes_applied

def fix_decorator_errors(content):
    """修复装饰器语法错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复装饰器后多余的冒号
    pattern = r'^(\s*@[\w\.]+.*)\s*:\s*$'
    replacement = r'\1'
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个装饰器后多余的冒号")
    
    return content, fixes_applied

def fix_string_errors(content):
    """修复字符串语法错误"""
    original_content = content
    fixes_applied = 0
    
    # 修复f-string语法错误
    # 移除无效的f-string标记
    pattern = r'f"([^"]*)":\s*([^,\n}\]]*)'
    replacement = r'f"\1": \2'
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        content = new_content
        fixes_applied += count
        logger.info(f"修复了 {count} 个f-string语法错误")
    
    return content, fixes_applied

def fix_specific_syntax_errors_in_file(file_path, dry_run=False, verbose=False):
    """修复单个文件中的特定语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        total_fixes = 0
        
        # 应用各种修复
        content, fixes = fix_colon_errors(content)
        total_fixes += fixes
        
        content, fixes = fix_assignment_errors(content)
        total_fixes += fixes
        
        content, fixes = fix_import_errors(content)
        total_fixes += fixes
        
        content, fixes = fix_bracket_errors(content)
        total_fixes += fixes
        
        content, fixes = fix_decorator_errors(content)
        total_fixes += fixes
        
        content, fixes = fix_string_errors(content)
        total_fixes += fixes
        
        # 验证修复后的语法
        if content != original_content and not validate_syntax(content):
            logger.warning(f"修复后语法仍然不正确: {file_path}")
            # 回滚到原始内容
            content = original_content
            total_fixes = 0
        
        # 如果有修改且语法正确，保存文件
        if content != original_content and validate_syntax(content):
            if verbose:
                logger.info(f"修复了 {file_path} 中的 {total_fixes} 个语法错误")
            
            if not dry_run:
                # 备份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已备份 {file_path} 到 {backup_path}")
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已修复并保存 {file_path}")
            else:
                logger.info(f"[DRY RUN] 将修复 {file_path} 中的 {total_fixes} 个语法错误")
            
            return total_fixes
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
        fixes = fix_specific_syntax_errors_in_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期报告进度
        if files_processed % 50 == 0:
            logger.info(f"已处理 {files_processed}/{len(python_files)} 个文件，修复了 {total_fixes} 个语法错误")
    
    logger.info(f"目录 {directory} 处理完成，共处理了 {files_processed} 个文件，修复了 {total_fixes} 个错误")
    return files_processed, total_fixes

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='最终精确修复脚本')
    parser.add_argument('--dir', type=str, default='.', help='要处理的目录')
    parser.add_argument('--dry-run', action='store_true', help='仅检查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"开始修复，时间: {start_time}")
    
    try:
        files_processed, total_fixes = fix_directory(
            args.dir, 
            dry_run=args.dry_run, 
            verbose=args.verbose
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修复完成，共处理了 {files_processed} 个文件，修复了 {total_fixes} 个错误")
        logger.info(f"总耗时: {duration:.2f} 秒")
        
        if args.dry_run:
            logger.info("这是一次试运行，没有实际修改任何文件")
        
        return 0
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())