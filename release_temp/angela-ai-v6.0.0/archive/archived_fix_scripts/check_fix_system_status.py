#!/usr/bin/env python3
"""
检查自动修复系统状态
"""

import sys
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
from pathlib import Path

def check_fix_system_status():
    """检查自动修复系统状态"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    print('=== 自动修复系统状态检查 ===')
    print(f'项目根目录, {project_root}')
    print(f'已加载模块, {len(engine.modules())}个')
    for fix_type, module in engine.modules.items():::
        print(f'  - {fix_type.value} {module.name}')
    
    # 分析整个项目状态
    context == FixContext(
        project_root=project_root,,
    scope == FixScope.PROJECT(),
        backup_enabled == True,
        dry_run == True,  # 先干运行分析
        ai_assisted == True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    print('\n=开始分析项目问题 ===')
    analysis = engine.analyze_project(context)
    
    print(f'\n发现的问题统计,')
    for fix_type, count in analysis['statistics'].items():::
        if count > 0,::
            print(f'  {fix_type} {count}个问题')
    
    total_issues = sum(analysis['statistics'].values())
    print(f'\n总问题数, {total_issues}')
    print('=' * 50)
    
    return analysis, engine, context

if __name'__main__':::
    analysis, engine, context = check_fix_system_status()