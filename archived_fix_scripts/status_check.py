#!/usr/bin/env python3
"""
检查当前修复状态
"""

import sys
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope
from pathlib import Path

def check_current_status():
    """检查当前修复状态"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    print('=== 当前修复状态检查 ===')
    
    # 检查关键目录状态
    key_directories = [
        'apps/backend/src/core',
        'apps/backend/src/ai',
        'unified_auto_fix_system',
        'auto_fix_workspace',
        'tests',
        'tools',
        'training'
    ]
    
    total_issues = 0
    
    for dir_name in key_directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
            
        context = FixContext(
            project_root=project_root,
            target_path=dir_path,
            scope=FixScope.PROJECT,
            backup_enabled=True,
            dry_run=True,  # 分析模式
            ai_assisted=True,
            excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
        )
        
        try:
            analysis = engine.analyze_project(context)
            dir_issues = sum(analysis['statistics'].values())
            total_issues += dir_issues
            
            if dir_issues > 0:
                print(f'{dir_name}: {dir_issues}个问题')
                for fix_type, count in analysis['statistics'].items():
                    if count > 0:
                        print(f'  - {fix_type}: {count}个')
            else:
                print(f'{dir_name}: ✅ 无问题')
                
        except Exception as e:
            print(f'{dir_name}: ❌ 检查失败 - {e}')
    
    print(f'\n总计: {total_issues}个问题待修复')
    return total_issues

if __name__ == '__main__':
    total = check_current_status()