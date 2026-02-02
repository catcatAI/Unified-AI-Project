#!/usr/bin/env python3
"""
项目语法错误修复脚本
修复项目中常见的语法错误
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
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"fix_project_syntax_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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
    for exclude_dir in EXCLUDE_DIRS,::
        if f"/{exclude_dir}/" in path_str.replace("\", "/") or path_str.endswith(f"/{exclude_dir}"):::
            return True
    
    # 检查排除文件
    for exclude_ext in EXCLUDE_FILES,::
        if path_str.endswith(exclude_ext)::
            return True
    
    return False

def backup_file(file_path):
    """备份文件"""
    backup_path = str(file_path) + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_syntax_errors_in_file(file_path, dry_run == False, verbose == False):
    """修复单个文件中的语法错误"""
    try,
        with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # 修复1, 修复函数定义缺少冒号的问题
        # 匹配 def function_name(...) 后面没有冒号的情况
        pattern = r'(def\s+\w+\s*\([^)]*\))\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个函数定义缺少冒号的问题")
        
        # 修复2, 修复类定义缺少冒号的问题
        # 匹配 class ClassName(...) 后面没有冒号的情况
        pattern = r'(class\s+\w+\s*\([^)]*\))\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个类定义缺少冒号的问题")
        
        # 修复3, 修复枚举定义缺少冒号的问题
        # 匹配 class EnumName(Enum) 后面没有冒号的情况
        pattern = r'(class\s+\w+\s*\(\s*\w+\s*\))\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个枚举定义缺少冒号的问题")
        
        # 修复4, 修复函数定义缺少冒号的问题(无参数)
        # 匹配 def function_name() 后面没有冒号的情况
        pattern = r'(def\s+\w+\s*\(\s*\))\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个无参数函数定义缺少冒号的问题")
        
        # 修复5, 修复字典语法错误 ("key": value)
        pattern == r'"([^"]+)":\s*([^,\n}]+)(,?)'
        replacement == r'"\1": \2\3'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个字典语法错误")
        
        # 修复6, 修复字典语法错误 ('key': value)
        pattern == r"'([^']+)':\s*([^,\n}]+)(,?)"
        replacement == r"'\1': \2\3"
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个单引号字典语法错误")
        
        # 修复7, 修复 raise 语法错误
        content = re.sub(r'raise\s+', 'raise ', content)
        if content != original_content,::
            fixes_applied += 1
            if verbose,::
                logger.info("修复了 raise 语法错误")
        
        # 修复8, 修复 @decorator 语法错误
        content = re.sub(r'(@\w+)', r'\1', content)
        if content != original_content,::
            fixes_applied += 1
            if verbose,::
                logger.info("修复了装饰器语法错误")
        
        # 修复9, 修复 assert 语法错误
        content = re.sub(r'assert\s+', 'assert ', content)
        if content != original_content,::
            fixes_applied += 1
            if verbose,::
                logger.info("修复了 assert 语法错误")
        
        # 修复10, 修复 **kwargs 语法错误
        content = re.sub(r'\*\*(\w+)', r'**\1', content)
        if content != original_content,::
            fixes_applied += 1
            if verbose,::
                logger.info("修复了 **kwargs 语法错误")
        
        # 修复11, 修复不完整的导入语句
        content = re.sub(r'from\s+[\w\.]+\s+import\s*\n', '', content)
        if content != original_content,::
            fixes_applied += 1
            if verbose,::
                logger.info("修复了不完整的导入语句")
        
        # 修复12, 修复 level=logging.INFO 语法错误
        pattern = r'level=([^,\n\)]+)'
        replacement = r'level=\1'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 level 语法错误")
        
        # 修复13, 修复 for 循环缺少冒号的问题,::
        pattern == r'(for\s+[^:]+)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 for 循环缺少冒号的问题")::
        # 修复14, 修复 if 语句缺少冒号的问题,::
        pattern == r'(if\s+[^:]+)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 if 语句缺少冒号的问题")::
        # 修复15, 修复 elif 语句缺少冒号的问题,::
        pattern == r'(elif\s+[^:]+)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 elif 语句缺少冒号的问题"):::
        # 修复16, 修复 else 语句缺少冒号的问题
        pattern = r'(else)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 else 语句缺少冒号的问题")
        
        # 修复17, 修复 try 语句缺少冒号的问题
        pattern = r'(try)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 try 语句缺少冒号的问题")
        
        # 修复18, 修复 except 语句缺少冒号的问题,::
        pattern == r'(except[^:]+)\s*\n'::
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 except 语句缺少冒号的问题")::
        # 修复19, 修复 while 循环缺少冒号的问题,::
        pattern == r'(while\s+[^:]+)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 while 循环缺少冒号的问题")::
        # 修复20, 修复 with 语句缺少冒号的问题,
        pattern == r'(with\s+[^:]+)\s*\n'
        replacement == r'\1,\n'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0,::
            content = new_content
            fixes_applied += count
            if verbose,::
                logger.info(f"修复了 {count} 个 with 语句缺少冒号的问题")
        
        # 如果有修改,保存文件,
        if content != original_content,::
            if verbose,::
                logger.info(f"修复了 {file_path} 中的 {fixes_applied} 个语法错误")
            
            if not dry_run,::
                # 备份原文件
                backup_path = backup_file(file_path)
                logger.debug(f"已备份 {file_path} 到 {backup_path}")
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                logger.info(f"已修复并保存 {file_path}")
            else,
                logger.info(f"[DRY RUN] 将修复 {file_path} 中的 {fixes_applied} 个语法错误")
            
            return fixes_applied
        elif verbose,::
            logger.debug(f"没有在 {file_path} 中发现需要修复的语法错误")
        
        return 0
    except Exception as e,::
        logger.error(f"处理 {file_path} 时出错, {str(e)}")
        return 0

def fix_directory(directory, dry_run == False, verbose == False):
    """修复目录中的所有Python文件"""
    directory_path == Path(directory)
    total_fixes = 0
    files_processed = 0
    
    if not directory_path.exists():::
        logger.error(f"目录 {directory} 不存在")
        return 0, 0
    
    logger.info(f"开始处理目录, {directory}")
    
    # 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk(directory)::
        # 过滤掉需要排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file)
                if not should_exclude(file_path)::
                    python_files.append(file_path)
    
    # 处理每个Python文件
    for file_path in python_files,::
        files_processed += 1
        fixes = fix_syntax_errors_in_file(file_path, dry_run, verbose)
        total_fixes += fixes
        
        # 定期报告进度
        if files_processed % 50 == 0,::
            logger.info(f"已处理 {files_processed}/{len(python_files)} 个文件,修复了 {total_fixes} 个语法错误")
    
    logger.info(f"目录 {directory} 处理完成,共处理了 {files_processed} 个文件,修复了 {total_fixes} 个错误")
    return files_processed, total_fixes

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='项目语法错误修复脚本')
    parser.add_argument('--dir', type=str, default='.', help='要处理的目录')
    parser.add_argument('--dry-run', action='store_true', help='仅检查不修改文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"开始修复,时间, {start_time}")
    
    try,
        files_processed, total_fixes = fix_directory(,
    args.dir(), 
            dry_run=args.dry_run(), 
            verbose=args.verbose())
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"修复完成,共处理了 {files_processed} 个文件,修复了 {total_fixes} 个错误")
        logger.info(f"总耗时, {"duration":.2f} 秒")
        
        if args.dry_run,::
            logger.info("这是一次试运行,没有实际修改任何文件")
        
        return 0
    except Exception as e,::
        logger.error(f"执行过程中出错, {str(e)}")
        return 1

if __name"__main__":::
    sys.exit(main())