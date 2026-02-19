#!/usr/bin/env python3
"""
为组件的initialize方法添加幂等性保护
"""

import re
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def add_idempotency_protection(file_path, class_name, has_async=True):
    """
    为类的initialize方法添加完整的幂等性保护
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有完整的幂等性保护
    if re.search(r'async\s+initialize\(\)\s*{[^}]*this\.isInitialized\s*===?\s*true', content, re.DOTALL):
        print(f"  ⚠️  {class_name} 已经有幂等性保护，跳过")
        return False
    
    # 查找initialize方法
    if has_async:
        pattern = r'(async\s+initialize\(\)\s*\{)'
    else:
        pattern = r'(initialize\(\)\s*\{)'
    
    match = re.search(pattern, content)
    if not match:
        print(f"  ❌ 未找到 {class_name}.initialize() 方法")
        return False
    
    # 幂等性检查代码
    indent = '        '
    protection_code = f'''
{indent}// 幂等性保护：防止重复初始化
{indent}if (this.isInitialized) {{
{indent}    console.log('[{class_name}] Already initialized, skipping');
{indent}    return true;
{indent}}}
'''
    
    # 替换
    new_content = content[:match.end()] + protection_code + content[match.end():]
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ {class_name} 添加幂等性检查成功")
    return True

def add_is_initialized_flag(file_path, class_name):
    """
    为类添加isInitialized标志（如果不存在）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有isInitialized
    if re.search(r'this\.isInitialized\s*=', content):
        return False
    
    # 在构造函数中添加isInitialized标志
    constructor_pattern = r'(class\s+' + re.escape(class_name) + r'[^{]*{(?:[^{}]|{[^{}]*})*?})(constructor\s*\([^)]*\)\s*\{)'
    match = re.search(constructor_pattern, content)
    
    if match:
        indent = '        '
        flag_code = f'{indent}this.isInitialized = false;\n'
        new_content = content[:match.end()] + flag_code + content[match.end():]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ {class_name} 添加isInitialized标志成功")
        return True
    
    return False

def set_initialized_flag_on_success(file_path, class_name):
    """
    在initialize方法末尾设置isInitialized标志（成功时）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找初始化成功的console.log
    patterns = [
        r"(console\.log\('\[?\w*Handler\]?\s*Initialized.*?\))",
        r"(console\.log\('Initialization complete.*?\))",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            # 检查后面是否已经有 this.isInitialized = true
            if re.search(r'this\.isInitialized\s*=\s*true;', content[match.end():match.end()+200]):
                return False
            
            flag_code = '\n        this.isInitialized = true;'
            new_content = content[:match.end()] + flag_code + content[match.end():]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  ✅ {class_name} 设置isInitialized标志成功")
            return True
    
    return False

def main():
    print("=" * 60)
    print("为组件的initialize方法添加幂等性保护")
    print("=" * 60)
    
    base_dir = Path('/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js')
    
    # 需要处理的组件
    components = [
        ('audio-handler.js', 'AudioHandler', True),
        ('haptic-handler.js', 'HapticHandler', True),
        ('hardware-detection.js', 'HardwareDetector', True),
    ]
    
    for file_name, class_name, has_async in components:
        file_path = base_dir / file_name
        
        if not file_path.exists():
            print(f"  ❌ 文件不存在: {file_name}")
            continue
        
        print(f"\n处理 {class_name} ({file_name})...")
        
        # 添加isInitialized标志
        add_is_initialized_flag(file_path, class_name)
        
        # 添加幂等性检查
        add_idempotency_protection(file_path, class_name, has_async)
        
        # 在初始化成功后设置标志
        set_initialized_flag_on_success(file_path, class_name)
    
    print("\n" + "=" * 60)
    print("幂等性保护添加完成")
    print("=" * 60)

if __name__ == '__main__':
    main()