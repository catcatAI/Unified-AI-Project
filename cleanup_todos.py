#!/usr/bin/env python3
"""
清理误导性的 TODO 注释
移除针对标准库和已安装第三方库的 "Fix import" TODO
"""
import re
from pathlib import Path
import sys

# 这些模块是 Python 标准库，不需要 try-except 或 TODO
STANDARD_LIBS = {
    'asyncio', 'typing', 'enum', 'uuid', 'websockets', 'threading', 
    'socket', 'smtplib', 'shutil', 'weakref', 'traceback', 'random',
    'time', 'json', 'logging', 'os', 'pathlib', 'dataclasses', 'importlib',
    'subprocess', 'datetime', 'collections', 'itertools', 'hashlib',
    'base64', 'zlib', 'pickle', 'csv', 'configparser', 'argparse',
    'signal', 'math', 're'
}

# 这些库在 requirements.txt 中已声明，应该直接导入
DECLARED_LIBS = {
    'numpy', 'yaml', 'psutil', 'speech_recognition', 'skimage', 
    'skimage.feature', 'huggingface_hub', 'msgpack', 'bz2', 'lzma'
}

# 需要保留的真实 TODO（非导入相关）
REAL_TODOS = {
    # 功能性 TODO
    ('ai/agents/agent_manager_extensions.py', 140),
    ('ai/dialogue/__init__.py', 2),
    # psutil 可选功能相关
    ('core/managers/execution_monitor.py', 35),
    ('core/managers/execution_monitor.py', 232),
    ('core/managers/execution_monitor.py', 508),
    ('core/managers/execution_monitor.py', 519),
    ('core/managers/execution_manager.py', 137),
}

def clean_todo_comment(line):
    """清理误导性的 TODO 注释"""
    # 匹配 "TODO: Fix import - module 'xxx' not found" 模式
    pattern = r'# TODO: Fix import - module [\'"]([^\'"]+)[\'"] not found'
    match = re.search(pattern, line)
    
    if match:
        module = match.group(1)
        # 如果是标准库或已声明的库，这个 TODO 是误导性的
        if module in STANDARD_LIBS or module in DECLARED_LIBS:
            # 直接移除整行
            return None
        # 否则保留 TODO
        return line
    
    return line

def process_file(file_path):
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        
        for i, line in enumerate(lines, 1):
            rel_path = str(file_path.relative_to('/home/cat/桌面/Unified-AI-Project/apps/backend/src'))
            
            # 检查是否是需要保留的真实 TODO
            if (rel_path, i) in REAL_TODOS:
                new_lines.append(line)
                continue
            
            # 尝试清理 TODO 注释
            cleaned = clean_todo_comment(line)
            if cleaned is None:
                modified = True
                print(f"  删除: {rel_path}:{i}")
            else:
                new_lines.append(cleaned)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"错误处理 {file_path}: {e}")
        return False

def main():
    base_path = Path('/home/cat/桌面/Unified-AI-Project/apps/backend/src')
    
    # 查找所有 .py 文件
    py_files = list(base_path.rglob('*.py'))
    
    print(f"找到 {len(py_files)} 个 Python 文件")
    print(f"正在清理误导性的 TODO 注释...\n")
    
    modified_count = 0
    for py_file in py_files:
        if process_file(py_file):
            modified_count += 1
    
    print(f"\n✅ 完成！共修改了 {modified_count} 个文件")

if __name__ == '__main__':
    main()
