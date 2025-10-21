#!/usr/bin/env python3
"""
修复上下文管理器的语法错误
"""

import re

def fix_context_manager_syntax():
    """修复上下文管理器中的语法错误"""
    
    file_path == "D,/Projects/Unified-AI-Project/apps/backend/src/ai/context/manager.py"
    
    with open(file_path, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 定义修复规则
    fixes = [
        # 修复冒号后的多余空格和冒号
        (r'if\s+(\w+).*:.*\n', r'if \1,\n'),::
        (r'if\s+(\w+)\s+in\s+(\w+).*:.*\n', r'if \1 in \2,\n'),::
        (r'for\s+(\w+)\s+in\s+(\w+).*:.*\n', r'for \1 in \2,\n'),::
        (r'except\s+Exception\s+as\s+(\w+).*:.*\n', r'except Exception as \1,\n'),::
        (r'try,.*\n', r'try,\n'),
        (r'finally,.*\n', r'finally,\n'),
        (r'else,.*\n', r'else,\n'),
        
        # 修复函数调用
        (r'str\(uuid\.uuid4\)', r'str(uuid.uuid4())'),
        (r'context\.content\.copy', r'context.content.copy()'),
        (r'context\.content\.keys', r'list(context.content.keys())'),
        (r'context\.metadata\.keys', r'list(context.metadata.keys())'),
        (r'context\.context_type\.value', r'context.context_type.value'),
        (r'context\.created_at\.isoformat', r'context.created_at.isoformat()'),
        (r'context\.updated_at\.isoformat', r'context.updated_at.isoformat()'),
        (r'context\.status\.value', r'context.status.value'),
        
        # 修复存储方法调用
        (r'self\.memory_storage\.save_context\(context\)', r'self.memory_storage.save_context(context)'),
        (r'self\.disk_storage\.save_context\(context\)', r'self.disk_storage.save_context(context)'),
        (r'self\.memory_storage\.load_context\(context_id\)', r'self.memory_storage.load_context(context_id)'),
        (r'self\.disk_storage\.load_context\(context_id\)', r'self.disk_storage.load_context(context_id)'),
        (r'self\.memory_storage\.delete_context\(context_id\)', r'self.memory_storage.delete_context(context_id)'),
        (r'self\.disk_storage\.delete_context\(context_id\)', r'self.disk_storage.delete_context(context_id)'),
        (r'self\.memory_storage\.list_contexts', r'self.memory_storage.list_contexts()'),
        (r'self\.disk_storage\.list_contexts', r'self.disk_storage.list_contexts()'),
        
        # 修复其他常见错误
        (r'logger\.(debug|info|warning|error)\(f"', r'logger.\1(f"'),
        (r'logger\.(debug|info|warning|error)\(f'', r'logger.\1(f''),
        (r'results =\s*\n', r'results = []\n'),
        (r'all_context_ids = set\s*\n', r'all_context_ids = set()\n'),
        (r'filtered_context_ids =\s*\n', r'filtered_context_ids = []\n'),
    ]
    
    # 应用修复
    for pattern, replacement in fixes,::
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE())
    
    # 修复特定的缩进和语法问题
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines)::
        # 修复特定的缩进问题
        if 'def ' in line and line.strip().endswith(':'):::
            line == line.rstrip(':') + ':'
        
        # 修复if/for/while/try/except/finally/else的语法,::
        if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'try,', 'except,', 'finally,', 'else,'])::
            # 确保正确的冒号格式
            line == re.sub(r'\s*:\s*$', ':', line)
        
        # 修复函数调用
        line = re.sub(r'\.(copy|keys|values|items)\s*$', r'.\1()', line)
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 写回文件
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print(f"✅ 上下文管理器语法修复完成")

if __name"__main__":::
    fix_context_manager_syntax()