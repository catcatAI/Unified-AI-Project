#!/usr/bin/env python3
"""
修复HSP连接器文件中的语法问题
"""

import re
from pathlib import Path

def fix_hsp_connector_syntax():
    """修复HSP连接器文件中的语法问题"""
    file_path = Path("apps/backend/src/core/hsp/connector.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复函数定义后的冒号问题
    # 修复 get_schema_uri 函数定义
    content = re.sub(
        r'def get_schema_uri\(schema_name: str\) -> str:\s*"""Constructs a file URI for a given schema name\."""',
        'def get_schema_uri(schema_name: str) -> str:\n    """Constructs a file URI for a given schema name."""',
        content
    )
    
    # 修复属性定义问题
    fixes = [
        # 修复属性定义中的冒号问题
        (r'(\s*@property\s*\n\s*def \w+\(self\))\s*:\s*(""".*?""")', r'\1:\n        \2'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 修复缩进问题
    # 修复 __init__ 方法中的缩进
    lines = content.split('\n')
    in_init_method = False
    init_indent_level = 0
    fixed_lines = []
    
    for line in lines:
        stripped = line.lstrip()
        
        # 检测 __init__ 方法开始
        if stripped.startswith('def __init__') and 'HSPConnector' in ''.join(fixed_lines[-3:]):
            in_init_method = True
            init_indent_level = len(line) - len(stripped)
            fixed_lines.append(line)
            continue
        
        # 检测 __init__ 方法结束
        if in_init_method and stripped and not line.startswith(' ' * (init_indent_level + 4)) and not stripped.startswith('def '):
            if init_indent_level > 0 and stripped not in ['else:', 'elif']:
                in_init_method = False
        
        # 修复 __init__ 方法中的缩进
        if in_init_method and stripped and not stripped.startswith('#'):
            # 确保代码行有正确的缩进
            if line.startswith(' ' * init_indent_level) and not line.startswith(' ' * (init_indent_level + 4)):
                if not stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'else:', 'elif')):
                    # 这是一个需要缩进的代码行
                    line = ' ' * (init_indent_level + 4) + stripped
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复HSP连接器文件中的语法问题: {file_path}")
    return True

def main():
    """主函数"""
    print("开始修复HSP连接器文件中的语法问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    import os
    os.chdir(project_root)
    
    # 修复文件
    if fix_hsp_connector_syntax():
        print("HSP连接器文件修复完成。")
    else:
        print("HSP连接器文件修复失败。")

if __name__ == "__main__":
    main()