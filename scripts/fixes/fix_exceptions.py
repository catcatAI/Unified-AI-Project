#!/usr/bin/env python3
"""
智能异常处理修复脚本
Intelligent Exception Handler Fixer
"""

import re
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 定义常见操作和对应的异常类型
EXCEPTION_MAPPING = {
    # 文件操作
    r'\.store\(': ['ValueError', 'TypeError', 'RuntimeError'],
    r'\.retrieve': ['ValueError', 'KeyError', 'IndexError'],
    r'open\(': ['IOError', 'OSError', 'FileNotFoundError', 'PermissionError'],
    r'\.load\(': ['IOError', 'OSError', 'FileNotFoundError'],
    r'\.save\(': ['IOError', 'OSError', 'PermissionError'],
    
    # 网络操作
    r'requests\.': ['requests.RequestException', 'requests.ConnectionError', 'requests.Timeout'],
    r'aiohttp': ['aiohttp.ClientError', 'aiohttp.ClientConnectorError'],
    r'\.post\(': ['aiohttp.ClientError', 'requests.RequestException'],
    r'\.get\(': ['aiohttp.ClientError', 'requests.RequestException'],
    
    # 导入操作
    r'import ': ['ImportError', 'ModuleNotFoundError'],
    r'from .* import': ['ImportError', 'ModuleNotFoundError'],
    
    # 类型转换
    r'int\(': ['ValueError', 'TypeError'],
    r'float\(': ['ValueError', 'TypeError'],
    r'json\.loads': ['json.JSONDecodeError', 'ValueError'],
    r'json\.load': ['json.JSONDecodeError', 'ValueError', 'IOError'],
    
    # 数学运算
    r'np\.': ['ValueError', 'TypeError', 'numpy.linalg.LinAlgError'],
    r'\.encode\(': ['UnicodeEncodeError', 'AttributeError'],
    r'\.decode\(': ['UnicodeDecodeError', 'AttributeError'],
    
    # 异步操作
    r'asyncio': ['asyncio.CancelledError', 'asyncio.TimeoutError'],
    r'await ': ['asyncio.CancelledError', 'RuntimeError'],
}

def find_try_blocks(content):
    """找到所有的try-except块"""
    lines = content.split('\n')
    blocks = []
    i = 0
    
    while i < len(lines):
        if lines[i].strip().startswith('try:'):
            # 找到try块
            try_start = i
            indent = len(lines[i]) - len(lines[i].lstrip())
            
            # 找到对应的except
            j = i + 1
            while j < len(lines):
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                if line_indent <= indent and (lines[j].strip().startswith('except ') or lines[j].strip().startswith('finally:')):
                    break
                j += 1
            
            if j < len(lines) and 'except Exception' in lines[j]:
                blocks.append((try_start, j, indent))
            i = j
        else:
            i += 1
    
    return blocks

def analyze_try_block(lines, start, end, indent):
    """分析try块内的代码，推断可能的异常类型"""
    try_content = '\n'.join(lines[start+1:end])
    
    suggested_exceptions = set()
    
    # 检查代码内容
    for pattern, exceptions in EXCEPTION_MAPPING.items():
        if re.search(pattern, try_content):
            suggested_exceptions.update(exceptions)
    
    # 如果没有找到特定模式，返回通用异常
    if not suggested_exceptions:
        suggested_exceptions = {'RuntimeError', 'ValueError'}
    
    return list(suggested_exceptions)[:3]  # 最多3个异常

def fix_file(filepath):
    """修复单个文件"""
    path = Path(filepath)
    if not path.exists():
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    blocks = find_try_blocks(content)
    
    if not blocks:
        return False
    
    fixed_count = 0
    # 从后向前修复，避免行号变化
    for start, end, indent in reversed(blocks):
        exceptions = analyze_try_block(lines, start, end, indent)
        
        # 构建新的except语句
        old_line = lines[end]
        # 提取原始缩进和logger调用
        match = re.match(r'(\s*)except Exception as e:\s*(.*)', old_line)
        if match:
            base_indent = match.group(1)
            rest = match.group(2)
            
            # 构建新的except行
            new_line = f"{base_indent}except ({', '.join(exceptions)}) as e:"
            if rest.strip():
                new_line += f"  {rest}"
            
            lines[end] = new_line
            fixed_count += 1
    
    if fixed_count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"✅ Fixed {fixed_count} bare exceptions in: {filepath}")
        return True
    
    return False

def main():
    """主函数"""
    print("=" * 70)
    print("🔧 Intelligent Exception Handler Fixer")
    print("=" * 70)
    
    # 关键文件列表
    critical_files = [
        "apps/backend/src/core/orchestrator.py",
        "apps/backend/src/ai/memory/hsm.py",
        "apps/backend/src/ai/learning/cdm.py",
        "apps/backend/src/ai/personality/template_manager.py",
    ]
    
    total_fixed = 0
    
    for filepath_str in critical_files:
        if fix_file(filepath_str):
            total_fixed += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Fixed {total_fixed} files")
    print("=" * 70)
    print("\nRemaining files need manual review:")
    print("- Services and utilities (lower priority)")
    print("- Backup and test files (can be ignored)")
    print("\nNote: Complex exception handling scenarios may need manual review")

if __name__ == "__main__":
    main()
