#!/usr/bin/env python3
"""
单文件修复脚本
"""

import sys
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
from pathlib import Path

def fix_single_file():
    """修复单个文件"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    # 修复HSP协议管理器
    target_file = project_root / 'apps/backend/src/core/hsp/protocol_manager.py'
    
    print(f'修复文件, {target_file}')
    
    context == FixContext(
        project_root=project_root,
        target_path=target_file,,
    scope == FixScope.PROJECT(),
        priority == FixPriority.NORMAL(),
        backup_enabled == True,
        dry_run == False,
        ai_assisted == True,
        custom_rules = {}
        excluded_paths=["node_modules", "__pycache__", ".git", "venv", ".venv"]
    )
    
    try,
        result = engine.fix_issues(context, specific_issues=['syntax_fix'])
        print(f'修复结果, {result.status}')
        print(f'发现问题, {result.issues_found}')
        print(f'修复问题, {result.issues_fixed}')
        
        if result.error_message,::
            print(f'错误信息, {result.error_message}')
            
        return result.issues_fixed > 0
        
    except Exception as e,::
        print(f'修复过程出错, {e}')
        import traceback
        traceback.print_exc()
        return False

if __name'__main__':::
    success = fix_single_file()
    print(f'修复成功, {success}')