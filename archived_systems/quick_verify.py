#!/usr/bin/env python3
"""
快速验证项目修复进度真实性
"""

import os
import sys
from pathlib import Path

def main():
    print("🔍 快速进度验证")
    print("=" * 40)
    
    # 1. 检查tests/conftest.py
    conftest = Path('tests/conftest.py')
    if conftest.exists():
        try:
            compile(conftest.read_text(), str(conftest), 'exec')
            print('✅ tests/conftest.py: 语法正确')
        except SyntaxError as e:
            print(f'❌ tests/conftest.py: 语法错误 - {e}')
    else:
        print('❌ tests/conftest.py: 文件不存在')
    
    # 2. 检查pytest
    try:
        import pytest
        print('✅ pytest: 可导入')
    except ImportError:
        print('❌ pytest: 无法导入')
    
    # 3. 检查统一修复系统
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        print('✅ 统一修复系统: 可加载')
    except Exception as e:
        print(f'❌ 统一修复系统: 加载失败 - {e}')
    
    # 4. 简单语法错误检查（只检查前50个文件）
    print('\n📊 语法错误抽样检查（前50个文件）:')
    count = 0
    errors = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    compile(content, str(filepath), 'exec')
                except SyntaxError:
                    errors += 1
                    if errors <= 3:
                        print(f'  ❌ {filepath}')
                except:
                    pass
                count += 1
                if count >= 50:
                    break
        if count >= 50:
            break
    
    print(f'样本检查: {count}个文件中{errors}个有语法错误')
    if errors > 0:
        print(f'估算总语法错误: 约{errors * 20}+个 (基于抽样)')
    else:
        print('✅ 样本中未发现语法错误')
    
    # 5. 检查一些具体文件的语法
    print('\n🔍 关键文件检查:')
    key_files = [
        'tests/conftest.py',
        'apps/backend/src/ai/agents/base_agent.py',
        'apps/backend/src/core/hsp/protocol.py'
    ]
    
    for filepath in key_files:
        path = Path(filepath)
        if path.exists():
            try:
                compile(path.read_text(), str(path), 'exec')
                print(f'  ✅ {filepath}')
            except SyntaxError as e:
                print(f'  ❌ {filepath} - {e}')
        else:
            print(f'  ⚠️  {filepath} - 文件不存在')

if __name__ == "__main__":
    main()