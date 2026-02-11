#!/usr/bin/env python3
"""
为关键方法添加错误返回值，让调用者知道错误
"""

import re
from pathlib import Path

def add_error_return_to_methods(file_path, methods_info):
    """
    为方法添加错误返回值
    
    Args:
        file_path: 文件路径
        methods_info: 方法信息列表 [{'name': 'methodName', 'return_on_error': 'return_value'}]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    for method_info in methods_info:
        method_name = method_info['name']
        return_on_error = method_info.get('return_on_error', 'false')
        
        # 查找方法中的catch块（更简单的模式）
        pattern = r'(catch\s*\([^)]+\)\s*\{)\s*(console\.(error|warn)\([^)]+\))\s*;\s*(\})'
        
        matches = list(re.finditer(pattern, content))
        
        for match in matches:
            # 获取方法名称以确认是正确的方法
            # 向前查找方法名
            method_name_pattern = r'(async\s+)?' + re.escape(method_name) + r'\([^)]*\)\s*\{'
            
            # 检查catch块之前是否有这个方法
            before_catch = content[max(0, match.start()-200):match.start()]
            if not re.search(method_name_pattern, before_catch):
                continue
            
            # 检查是否已经有返回值
            catch_block = content[match.start():match.end()]
            if 'return' in catch_block:
                continue
            
            # 添加返回值
            catch_content = match.group(1)
            after_log = match.group(2)
            closing_brace = match.group(4)
            
            new_catch = catch_content + '\n            ' + after_log + ';\n            return ' + return_on_error + ';\n        ' + closing_brace
            
            content = content[:match.start()] + new_catch + content[match.end():]
            modified = True
            print(f"  ✅ {method_name}: 添加错误返回值 {return_on_error}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified

def main():
    print("=" * 60)
    print("为方法添加错误返回值")
    print("=" * 60)
    
    base_dir = Path('/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js')
    
    # 定义需要改进的方法
    files_to_improve = [
        # Live2DManager
        {
            'file': 'live2d-manager.js',
            'methods': [
                {'name': 'loadModel', 'return_on_error': 'false'},
                {'name': 'setExpression', 'return_on_error': 'false'},
                {'name': 'setMotion', 'return_on_error': 'false'},
            ]
        },
        # StateMatrix
        {
            'file': 'state-matrix.js',
            'methods': [
                {'name': 'handleInteraction', 'return_on_error': 'false'},
                {'name': 'setLive2DManager', 'return_on_error': 'false'},
                {'name': 'setWebSocket', 'return_on_error': 'false'},
            ]
        },
        # HapticHandler
        {
            'file': 'haptic-handler.js',
            'methods': [
                {'name': 'triggerHaptic', 'return_on_error': 'false'},
                {'name': 'discoverDevices', 'return_on_error': '[]'},
            ]
        },
    ]
    
    for file_info in files_to_improve:
        file_path = base_dir / file_info['file']
        
        if not file_path.exists():
            print(f"\n❌ 文件不存在: {file_info['file']}")
            continue
        
        print(f"\n处理 {file_info['file']}...")
        
        add_error_return_to_methods(file_path, file_info['methods'])
    
    print("\n" + "=" * 60)
    print("错误返回值添加完成")
    print("=" * 60)

if __name__ == '__main__':
    main()